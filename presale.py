from quart import Quart, request, jsonify
from helpers import (create_mysql_connection, sendMessage, sendKeyboardMarkup, handle_config, handle_logger, sendReplyAPIKwargs, replyMessage)
import telegram
import json
import requests
from time import sleep
import asyncio
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, MessageEntity

BOT_TOKEN, BOT_CREATOR_ID, LOG_PATH, TELEGRAM_API_BASE_URL, WEBHOOK_URL, WHITELIST_TOKEN, PRESALE_TOKEN = handle_config()

app = Quart(__name__)
bot = telegram.Bot(token=PRESALE_TOKEN)
logger = handle_logger(LOG_PATH, 'presale')

presale_valid_flag = False

@staticmethod
def first_keyboard():
    keyboard = [[InlineKeyboardButton("Выполнено", callback_data='Done')],
                [InlineKeyboardButton("MAC", callback_data='MAC'),
                InlineKeyboardButton("Phone", callback_data='Phone'),
                InlineKeyboardButton("История", callback_data='History')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

@app.route('/presale', methods=['POST'])
async def webhook():
    data = await request.get_json()
    if 'message' in data:
        if 'text' in data['message']:
            print('data: ', data)
            message = data['message']['text']
            chat_id = data['message']['chat']['id']
            sender = data['message']['from']['id']

            if message.startswith('/presale') and data['message']['chat']['type'] == 'private' and data['message']['from']['is_bot'] == False:
                split_message = message.split()
                if len(split_message) == 2:
                    presale_url = split_message[1]
                    global presale_valid_flag
                    if not presale_valid_flag:
                        MIN_BUY, MAX_BUY, END_TIME, PRESALE_ADDRESS = get_html(presale_url)
                        if MIN_BUY is not None and MAX_BUY is not None and END_TIME is not None and PRESALE_ADDRESS is not None:
                                await sendMessage(chat_id, "Presale URL is valid", bot)
                                logger.info({'min_buy': MIN_BUY, 'max_buy': MAX_BUY, 'end_time': END_TIME, 'presale_address': PRESALE_ADDRESS})
                                presale_valid_flag = True

                                await sendKeyboardMarkup(chat_id, "Выберите действие", bot, first_keyboard())
                        else:
                            logger.error("Presale URL is invalid")
                            await sendMessage(chat_id, "Presale URL is invalid", bot)
                else:
                    logger.error("Invalid command")
                    await sendMessage(chat_id, "Invalid command", bot)
    if 'callback_query' in data:
        print('result_data: ', data)
        chat_id = data['callback_query']['message']['chat']['id']
        callback_data = data['callback_query']['data']
        _from = data['callback_query']['from']['username']

        if callback_data == 'Phone':
            api_kwargs = {
                'reply_markup': json.dumps({'force_reply': True}),
                'text': { 'text': 'Please send your phone number', 'text2': 'Please send your phone number2' },
            }
            await sendReplyAPIKwargs(chat_id, "Please send your PinkSale URL", bot, api_kwargs)
    return jsonify({"presale": True}), 200

def get_html(url):
    response = requests.get(url)

    END_TIME = None
    MAX_BUY = None
    MIN_BUY = None
    PRESALE_ADDRESS = None

    if response.status_code == 200:
        options = Options()
        options.add_argument('--headless')
        with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) as driver:
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

                WebDriverWait(tbody, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'tr')))
                rows = tbody.find_elements(By.TAG_NAME, 'tr')

                max_buy_amount = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//td[text()='Maximum Buy']")))
                min_buy_amount = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//td[text()='Minimum Buy']")))
                presale_address = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//td[text()='Presale Address']")))

                if len(rows) > 14:
                    target_row = rows[14]

                    # Scroll to the target row
                    driver.execute_script("arguments[0].scrollIntoView();", target_row)

                    sleep(2)

                    WebDriverWait(target_row, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'has-text-right')))
                    expected = target_row.find_element(By.CLASS_NAME, 'has-text-right')
                    target_row_html = expected.get_attribute('innerHTML')
                    target_row_html = target_row_html.split('(')[0].strip()
                    target_row_html = datetime.strptime(target_row_html, '%Y.%m.%d %H:%M')
                    END_TIME = int(target_row_html.timestamp())

                    if max_buy_amount and min_buy_amount and presale_address:
                        MAX_BUY = max_buy_amount.find_element(By.XPATH, './following-sibling::td').text.strip().split(' ')[0]
                        MIN_BUY = min_buy_amount.find_element(By.XPATH, './following-sibling::td').text.strip().split(' ')[0]
                        PRESALE_ADDRESS = presale_address.find_element(By.XPATH, './following-sibling::td').text.strip()
            except Exception as e:
                logger.error(e)
                print(e)
    
    return MIN_BUY, MAX_BUY, END_TIME, PRESALE_ADDRESS
    
if __name__ == '__main__':
    app.run(debug=True, port=8443)