from quart import Quart, request, jsonify
from helpers import (create_mysql_connection, sendMessage, handle_config)
import telegram
import requests
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
                    presale_html_content = get_html(presale_url)
                    if presale_html_content:
                        await sendMessage(chat_id, "Presale URL is valid", bot)
                        print(presale_html_content)
                    else:
                        await sendMessage(chat_id, "Presale URL is invalid", bot)
                else:
                    await sendMessage(chat_id, "Invalid command", bot)
    return jsonify({"presale": True}), 200

def get_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        sleep(2)
        driver.get(url)
        sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        sleep(2)
        parent_div = soup.find('div', class_='ant-card-body')
        sleep(2)
        if parent_div:
            table_container_div = parent_div.find('div', class_='table-container')
            print('table_container_div: ', table_container_div)
            sleep(2)
            if table_container_div:
                table = table_container_div.find('table')
                print('table: ', table)
                sleep(2)
                if table:
                    tbody = table.find('tbody')
                    print('tbody: ', tbody)
                    sleep(2)
                    if tbody:
                        rows = tbody.find_all('tr')
                        print('rows: ', rows)
                        print('len(rows): ', len(rows))
                        sleep(2)
                        if len(rows) > 14:
                            target_row = rows[14]
                            print('target_row2: ', target_row)
                            sleep(2)
                            if target_row:
                                sleep(2)
                                print('target_row: ', target_row)
                                return target_row

        driver.close()
        sleep(2)
        return parent_div
        # soup = BeautifulSoup(response.text, 'html.parser')
        # parent_div = soup.find('div', {'class': 'ant-card-body'})
        # print('parent_div: ', soup)
        # return parent_div
    else:
        return None
    
if __name__ == '__main__':
    app.run(debug=True, port=8443)