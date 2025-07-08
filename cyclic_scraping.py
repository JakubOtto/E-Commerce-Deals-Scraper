import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import telegram
import asyncio
from dotenv import load_dotenv


# Stałe
BASE_URL = "https://www.vinted.pl/catalog"
KNOWN_IDS_FILE = "known_ids.json"
ITEMS_FILE = "filtered_items.json"

# Funkcja do wysyłania powiadomień przez Telegram (async)
async def send_telegram_message(bot, chat_id, message, is_channel=False):
    try:
        if is_channel:
            chat_id_to_use = f"@{chat_id}" if not chat_id.startswith('-100') else chat_id
            await bot.send_message(chat_id=chat_id_to_use, 
                               text=message, 
                               parse_mode='HTML')
        else:
            await bot.send_message(chat_id=chat_id, 
                               text=message, 
                               parse_mode='HTML')
    except Exception as e:
        print(f"Błąd wysyłania powiadomienia Telegram: {str(e)}")

# Wczytaj konfigurację
def load_config():
    load_dotenv()
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Nie znaleziono pliku config.json - używam domyślnych ustawień")
        config = {
            "search_text": "koszulka ralph lauren",
            "max_price": 20,
            "min_price": 0,
            "refresh_minutes": 5,
            "search_keywords": ["ralph", "lauren", "polo"],
            "telegram": {
                "bot_token": "TOKEN",
                "chat_id": "ID",
                "channel_id": "ID"
            }
        }
    if "telegram" not in config:
        config["telegram"] = {}
    config["telegram"]["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN", config["telegram"].get("bot_token", ""))
    config["telegram"]["chat_id"] = os.getenv("TELEGRAM_CHAT_ID", config["telegram"].get("chat_id", ""))
    config["telegram"]["channel_id"] = os.getenv("TELEGRAM_CHANNEL_ID", config["telegram"].get("channel_id", ""))

    return config

# Wczytaj zapisane dane
def load_saved_data():
    known_ids = set()
    items = []
    
    if os.path.exists(KNOWN_IDS_FILE):
        try:
            with open(KNOWN_IDS_FILE, "r", encoding="utf-8") as f:
                known_ids = set(json.load(f))
        except:
            print("Nie udało się wczytać known_ids.json")
    
    if os.path.exists(ITEMS_FILE):
        try:
            with open(ITEMS_FILE, "r", encoding="utf-8") as f:
                items = json.load(f)
        except:
            print("Nie udało się wczytać filtered_items.json")
    
    return known_ids, items

# Zapisz dane
def save_data(known_ids, items):
    with open(KNOWN_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(known_ids), f, ensure_ascii=False, indent=2)
    
    with open(ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

# Sprawdź czy tytuł zawiera słowa kluczowe
def contains_keywords(title, keywords):
    if not keywords:  # jeśli lista jest pusta, akceptuj wszystkie ogłoszenia
        return True
    title_lower = title.lower()
    return any(keyword.lower() in title_lower for keyword in keywords)

# Główna funkcja scrapująca
async def scrape_ads(driver, config, bot, known_ids, items):
    # Przygotuj URL - zawsze sortowanie po najnowszych
    search_text = config["search_text"].replace(" ", "%20")
    url = f"{BASE_URL}?search_text={search_text}&order=newest_first"
    print(f"\n Sprawdzam nowe ogłoszenia: {url}")
    driver.get(url)
    time.sleep(5)  # Poczekaj na załadowanie
    
    # Znajdź wszystkie ogłoszenia
    ads = driver.find_elements(By.CSS_SELECTOR, 'div.feed-grid__item')
    print(f"Znaleziono {len(ads)} ogłoszeń")
    new_items_found = False
    
    # Przejrzyj każde ogłoszenie
    for ad in ads:
        try:
            # Pobierz link i sprawdź czy to ogłoszenie
            link = ad.find_element(By.TAG_NAME, "a").get_attribute("href")
            if not link or "/items/" not in link:  # Sprawdź czy to link do ogłoszenia
                print(" Pomijam - to nie jest link do ogłoszenia")
                continue
            # Pobierz cenę
            try:
                price_text = ad.find_element(By.CSS_SELECTOR, 
                            'span.web_ui__Text__subtitle.web_ui__Text__clickable').text
                price = float(price_text.replace("zł", "").replace(",", ".").strip())
            except:
                print("Pomijam - nie można odczytać ceny")
                continue
            # Sprawdź czy cena jest odpowiednia
            if price > config["max_price"] or price < config.get("min_price", 0):
                continue
            
            # Pobierz ID
            item_id = link.split("-")[-1] + " " + str(price)
            # Sprawdź czy już znaleziono to ogłoszenie
            if item_id in known_ids:
                continue
            print(f"Znaleziono nowe ogłoszenie za {price} zł")
            
            # Otwórz ogłoszenie w nowej karcie
            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(6)  # Poczekaj na załadowanie
            
            try:
                # Sprawdź czy to na pewno strona ogłoszenia
                if not driver.find_elements(By.CSS_SELECTOR, 
                                            '[data-testid="item-page-summary-plugin"]'):
                    print("Pomijam - nie znaleziono elementów ogłoszenia")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue
                # Pobierz szczegóły
                title = driver.find_element(By.CSS_SELECTOR, 
                            '[data-testid="item-page-summary-plugin"]').text.strip()
                # Sprawdź czy tytuł zawiera słowa kluczowe
                if not contains_keywords(title, config.get("search_keywords", [])):
                    print(f"Pomijam ogłoszenie - brak słów kluczowych w tytule: {title}")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    continue
                
                size = driver.find_element(By.CSS_SELECTOR, 
                                           '[itemprop="size"]').text.strip()
                condition = driver.find_element(By.CSS_SELECTOR, 
                                                '[itemprop="status"]').text.strip()
                # Zapisz nowe ogłoszenie
                known_ids.add(item_id)
                items.append({
                    "title": title,
                    "price": price,
                    "size": size,
                    "condition": condition,
                    "url": link,
                    "found_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                new_items_found = True
                
                # Wyślij powiadomienie przez Telegram
                message = f"""
🔔 <b>Nowe ogłoszenie!</b>

💰 Cena: {price} zł
👕 Rozmiar: {size}
📝 Stan: {condition}
🔗 <a href="{link}">Link do ogłoszenia</a>
"""
                # Wyślij na kanał
                if "channel_id" in config["telegram"]:
                    await send_telegram_message(bot, config["telegram"]["channel_id"], 
                                                message, is_channel=True)
                # Wyślij też wiadomość prywatną
                await send_telegram_message(bot, config["telegram"]["chat_id"], message)
            except Exception as e:
                print(f" Błąd przy przetwarzaniu ogłoszenia: {e}")
            finally:
                # Zamknij kartę i wróć do głównej
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(6)
        except Exception as e:
            print(f" Błąd przy przetwarzaniu ogłoszenia: {e}")
            continue
    # Zapisz dane jeśli znaleziono nowe ogłoszenia
    if new_items_found:
        save_data(known_ids, items)
        print(f" Zapisano {len(items)} ogłoszeń")
    return known_ids, items

async def main():
    # Wczytaj konfigurację
    config = load_config()
    
    # Wczytaj zapisane dane
    known_ids, items = load_saved_data()
    
    # Inicjalizuj bota Telegram
    bot = telegram.Bot(token=config["telegram"]["bot_token"])
    
    # Uruchom przeglądarkę
    options = Options()
    driver = webdriver.Chrome(options=options)
    
    print(" Uruchamiam scraper...")
    # Powiadom o uruchomieniu
    if "channel_id" in config["telegram"]:
        await send_telegram_message(bot, config["telegram"]["channel_id"], " Scraper został uruchomiony!", is_channel=True)
    await send_telegram_message(bot, config["telegram"]["chat_id"], " Scraper został uruchomiony!")
    
    try:
        while True:
            # Scrapuj ogłoszenia
            known_ids, items = await scrape_ads(driver, config, bot, known_ids, items)
            
            # Poczekaj przed następnym sprawdzeniem
            wait_time = config["refresh_minutes"] * 60
            print(f"\n Czekam {config['refresh_minutes']} minut przed sprawdzeniem nowych ogłoszeń...")
            time.sleep(wait_time)
            
            # Odśwież stronę
            driver.refresh()
            
    except KeyboardInterrupt:
        print("\n Zatrzymano skrypt")
        # Powiadom o zatrzymaniu
        if "channel_id" in config["telegram"]:
            await send_telegram_message(bot, config["telegram"]["channel_id"], " Scraper został zatrzymany!", is_channel=True)
        await send_telegram_message(bot, config["telegram"]["chat_id"], " Scraper został zatrzymany!")
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
