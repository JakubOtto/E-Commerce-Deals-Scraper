from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
driver = webdriver.Chrome()

url = "https://www.vinted.pl/catalog?search_text=koszulka%20ralph%20lauren&order=newest_first&disabled_personalization=true"
driver.get(url)
driver.implicitly_wait(5)

time.sleep(5)

ads = driver.find_elements(By.CSS_SELECTOR, 'div.feed-grid__item')

print(f"Znaleziono {len(ads)} ogłoszeń na pierwszej stronie:\n")

results = []

for ad in ads:
    try:
        # Cena
        price_text = ad.find_element(By.CSS_SELECTOR, 'span.web_ui__Text__subtitle.web_ui__Text__clickable').text.strip()
        price_value = float(price_text.replace("zł", "").replace(",", ".").strip())

        if price_value < 20:
            # Otwórz link w nowej karcie
            link = ad.find_element(By.TAG_NAME, "a").get_attribute("href")
            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[-1])

            # Poczekaj aż się załaduje szczegóły
            time.sleep(5)  

            # Zbierz dane
            title = driver.find_element(By.CSS_SELECTOR, '[data-testid="item-page-summary-plugin"]').text.strip()
            size = driver.find_element(By.CSS_SELECTOR, '[itemprop="size"]').text.strip()
            condition = driver.find_element(By.CSS_SELECTOR, '[itemprop="status"]').text.strip()

            results.append({
                "title": title,
                "price": price_value,
                #"size": size,
                "condition": condition,
                "url": link
            })

            # Zamknij kartę i wróć
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    except Exception as e:
        print("Błąd:", e)
        continue

# Zapisz do pliku JSON
with open("filtered_items.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Zapisano {len(results)} wyników.")


input("\nWciśnij Enter, aby zamknąć...")
driver.quit()
