import re
import csv
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def parse_player_data(script_text):
    data = {}
    patterns = {
        'fullname': r"var fullname = '(.*?)';",
        'currentrank': r"var currentrank = (\d+);",
        'peakrank': r"var peakrank = (\d+);",
        'dob': r"var dob = (\d+);",
        'ht': r"var ht = (\d+);",
        'country': r"var country = '(.*?)';",
        'elo_rating': r"var elo_rating = '(\d+)';"
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, script_text)
        if match:
            data[key] = match.group(1)
    return data

def parse_match_history(soup):
    table = soup.find('table', {'id': 'recent-results'})
    if not table:
        print("❌ Таблица с историей матчей не найдена в HTML")
        return [], []
    
    try:
        headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all('td')]
            rows.append(cells)
        return headers, rows
    except Exception as e:
        print(f"❌ Ошибка при парсинге таблицы: {e}")
        return [], []

def main(url):
    # Настройка Selenium (Chrome в headless-режиме)
    options = Options()
    options.add_argument("--headless")  # Запуск без открытия браузера
    options.add_argument("--disable-blink-features=AutomationControlled")  # Обход защиты от ботов
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        print("🌐 Загружаю страницу...")
        driver.get(url)
        time.sleep(3)  # Ждём загрузки JS
        
        # Получаем HTML после выполнения JavaScript
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Сохраняем HTML для отладки
        with open('debug_selenium.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        # Парсинг данных игрока
        player_data = {}
        script = soup.find('script', string=re.compile('var fullname'))
        if script:
            player_data = parse_player_data(script.text)
            print(f"✅ Данные игрока: {player_data.get('fullname', 'Неизвестно')}")
        else:
            print("❌ Данные игрока не найдены")

        # Парсинг истории матчей
        match_headers, match_rows = parse_match_history(soup)
        
        # Сохранение в CSV
        if player_data:
            with open('player_data.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=player_data.keys())
                writer.writeheader()
                writer.writerow(player_data)
        
        if match_headers and match_rows:
            with open('match_history.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(match_headers)
                writer.writerows(match_rows)
            print("✅ История матчей сохранена в match_history.csv")
        else:
            print("❌ История матчей не найдена (проверьте debug_selenium.html)")
    
    except Exception as e:
        print(f"🚨 Ошибка: {e}")
    finally:
        driver.quit()  # Закрываем браузер

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='URL страницы игрока на TennisAbstract.com')
    args = parser.parse_args()
    main(args.url)