# Vint / ed Scraper

A script for automatic monitoring of listings on [Vint**. / pl](https://www.vint**. / pl) according to specified criteria, with notifications sent to Telegram. 

--- 

## Features - Searching Vint / ed for new listings based on selected keywords and price limits. 
- Notifications about new offers sent to Telegram (channel and/or private).
- Saving found listings to a JSON file to avoid duplicates.
- Automatic refreshing and monitoring at defined intervals.

--- 

## Requirements 
- Python 3.8 or higher
- Google Chrome + ChromeDriver matching your Chrome version (placed in PATH)
- Python libraries:
  - selenium
  - python-telegram-bot
  - python-dotenv (optional)

--- 

## Installation 
1. **Clone the repository:** 
```bash
git clone https://github.com/your_username/vinted-scraper-final.git
cd vinted-scraper-final
``` 
3. **Install required libraries:** 
```bash
pip install -r requirements.txt
``` 

--- 

## Configuration 
1. Edit the `config.json` file in the root directory of the project.
  - `search_text` is the search query for the portal’s website,
  - `max_price` is the maximum price that meets your criteria,
  - `min_price` is the minimum price that meets your criteria,
  - `refresh_minutes` defines the time interval (in minutes) for re-running the scraper,
  - `search_keywords` allows you to input keywords; if none appear in the listing title, the scraper will neither save nor notify about that listing.

2. Sample `config.json` content:
  ```bash
  {
    "search_text": "koszulka ralph lauren",
    "max_price": 20,
    "min_price": 0,
    "refresh_minutes": 5,
    "search_keywords": ["ralph", "lauren", "polo"],
    "telegram": {
      "bot_token": "TWÓJ_TELEGRAM_BOT_TOKEN",
      "chat_id": "TWÓJ_TELEGRAM_CHAT_ID",
      "channel_id": "TWÓJ_TELEGRAM_CHANNEL_ID"
    }
  }
  ```
4. You can also set environment variables in a `.env` file to override values in `config.json`:
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
  - `TELEGRAM_CHANNEL_ID`
   
--- 

## Running After activating your virtual environment, start the scraper with: 
```bash 
python cyclic_scraping.py
``` 

--- 

## Important Information 
- This project is strictly educational and aims to demonstrate skills and practical applications of data scraping and automation techniques. It is not a commercial project
- I do not sell it nor encourage violating website terms of service.
- The main functionality of this project is cyclic scraping (`cyclic_scraping.py`) — regularly and repeatedly monitoring new listings based on defined criteria. Additionally, there is `just_scraping.py`, which allows one-time data extraction from a user-supplied link.

