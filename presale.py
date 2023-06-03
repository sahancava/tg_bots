from quart import Quart, request, jsonify
from helpers import (create_mysql_connection, sendMessage, handle_config)
import telegram
import requests
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BOT_TOKEN, BOT_CREATOR_ID, LOG_PATH, TELEGRAM_API_BASE_URL, WEBHOOK_URL, WHITELIST_TOKEN, PRESALE_TOKEN = handle_config()

app = Quart(__name__)
bot = telegram.Bot(token=PRESALE_TOKEN)

@app.route('/presale', methods=['POST'])
async def webhook():
    data = await request.get_json()
    if 'message' in data:
        if 'text' in data['message']:
            message = data['message']['text']
            chat_id = data['message']['chat']['id']
            sender = data['message']['from']['id']
            if message.startswith('/presale') and data['message']['chat']['type'] == 'private' and data['message']['from']['is_bot'] == False:
                split_message = message.split()
                if len(split_message) == 2:
                    presale_url = split_message[1]
                    presale_html_content = await get_html(presale_url)
                    if presale_html_content:
                        await sendMessage(chat_id, "Presale URL is valid", bot)
                        print(presale_html_content)
                    else:
                        await sendMessage(chat_id, "Presale URL is invalid", bot)
                else:
                    await sendMessage(chat_id, "Invalid command", bot)
    return jsonify({"presale": True}), 200

async def get_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)
        
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ant-card-body')))
            parent_div = driver.find_element(By.CLASS_NAME, 'ant-card-body')
            WebDriverWait(parent_div, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'table-container')))
            table_container_div = parent_div.find_element(By.CLASS_NAME, 'table-container')
            
            WebDriverWait(table_container_div, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            table = table_container_div.find_element(By.TAG_NAME, 'table')
            
            WebDriverWait(table, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'tbody')))
            tbody = table.find_element(By.TAG_NAME, 'tbody')
            # tbody_html = tbody.get_attribute('innerHTML')
            # print('tbody_html: ', tbody_html)
            
            WebDriverWait(tbody, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'tr')))
            rows = tbody.find_elements(By.TAG_NAME, 'tr')
            rows_html = rows[14].get_attribute('innerHTML')
            print('rows_html: ', rows_html)

            if len(rows) > 14:
                target_row = rows[14]
                
                WebDriverWait(target_row, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))
                needed_td = target_row.find_elements(By.TAG_NAME, 'td')[1]
                
                # if needed_td:
                #     needed_text = needed_td.get_text(strip=True)
                #     datetime_str = needed_text.split('(')[0].strip()
                #     datetime_obj = datetime.strptime(datetime_str, '%Y.%m.%d %H:%M')
                #     return datetime_obj

                return 1
        
        finally:
            driver.quit()
    
    return None
    # response = requests.get(url)
    # if response.status_code == 200:
    #     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    #     sleep(2)
    #     driver.get(url)
    #     sleep(2)
    #     soup = BeautifulSoup(driver.page_source, 'html.parser')
    #     sleep(2)
    #     parent_div = soup.find('div', class_='ant-card-body')
    #     sleep(2)
    #     if parent_div:
    #         table_container_div = parent_div.find('div', class_='table-container')
    #         sleep(2)
    #         if table_container_div:
    #             table = table_container_div.find('table')
    #             sleep(2)
    #             if table:
    #                 tbody = table.find('tbody')
    #                 sleep(2)
    #                 if tbody:
    #                     rows = tbody.find_all('tr')
    #                     sleep(2)
    #                     if len(rows) > 14:
    #                         target_row = rows[14]
    #                         sleep(2)
    #                         if target_row:
    #                             sleep(2)
    #                             needed_td = target_row.find_all('td')[1]
    #                             sleep(2)
    #                             if needed_td:
    #                                 needed_text = needed_td.get_text(strip=True)
    #                                 datetime_str = needed_text.split('(')[0].strip()
    #                                 datetime_obj = datetime.strptime(datetime_str, '%Y.%m.%d %H:%M')
    #                             return datetime_obj

    #     driver.close()
    #     sleep(2)
    #     return parent_div
    # else:
    #     return None
    
if __name__ == '__main__':
    app.run(debug=True, port=8443)