import mysql.connector
import configparser
import uuid
import sys
import json
import glob
import os
import time
import logging
import logging.handlers

config = configparser.ConfigParser()
config.read('config.ini')

def handle_config():
    BOT_TOKEN = config['DEFAULT']['TOKEN']
    BOT_CREATOR_ID = config['DEFAULT']['BOT_CREATOR_ID']
    LOG_PATH = config['DEFAULT']['LOG_PATH']
    WHITELIST_TOKEN = config['DEFAULT']['WHITELIST_TOKEN']
    PRESALE_TOKEN = config['DEFAULT']['PRESALE_TOKEN']
    TELEGRAM_API_BASE_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/'
    WEBHOOK_URL = 'hello-world'
    return BOT_TOKEN, BOT_CREATOR_ID, LOG_PATH, TELEGRAM_API_BASE_URL, WEBHOOK_URL, WHITELIST_TOKEN, PRESALE_TOKEN
async def create_mysql_connection():
    try:
        cnx = await mysql.connector.connect(user=config['DATABASE']['DB_USER'], password=config['DATABASE']['DB_PASSWORD'], host=config['DATABASE']['DB_HOST'], database=config['DATABASE']['DB_NAME'])
        return cnx
    except mysql.connector.Error as err:
        return None
async def sendMessage(chat_id, text, bot):
    try:
        async with bot as _bot:
            await _bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        await bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def handle_help_command(data, bot, BOT_CREATOR_ID, logger):
    chat_id = data['message']['chat']['id']
    from_id = data['message']['from']['id']
    if int(BOT_CREATOR_ID) == int(data['message']['from']['id']):
        response_text = 'Hello! Please enter a command (use /addAnother or /removeAnother).'
    else:
        response_text = 'To check if you win, please use the pattern\n(/checker MYWALLETADDRESS)'
    await sendMessage(chat_id, response_text, bot)
    logger.info('Help command executed by {} ({}).'.format(from_id, chat_id))
async def validate_contract_address(contract_address):
    if len(contract_address) < 1:
        return "Please provide a contract address to add"
    elif len(contract_address) != 42 or not contract_address.startswith("0x"):
        return "Invalid contract address"
    else:
        return None
async def removeLogFiles(chat_id, _bot, logger):
    try:
        list_of_files = glob.glob('logs/*')
        for file in list_of_files:
            os.remove(file)
        await sendMessage(chat_id, "All log files have been removed.", _bot)
    except Exception as e:
        line_number = sys._getframe().f_lineno
        error_string = "Error: {} on line {}".format(e, line_number)
        logger.error(error_string)
        await sendMessage(chat_id, error_string, _bot)
async def handle_add_another_command(data, _bot, logger):
    chat_id = data['message']['chat']['id']
    sender = data['message']['from']['id']
    ifOwner = await getChatAdministrators(chat_id, int(sender), _bot)
    random_password = int(uuid.uuid4())

    if ifOwner != True:
        response_text = "You are not the owner of this group!"
    else:
        chat_message = data['message']['text']
        split_message = chat_message.split()
        group_owner = data['message']['from']['id']

        if len(split_message) == 2:
            contract_address = split_message[1]

            contract_address_error = await validate_contract_address(contract_address)

            if contract_address_error:
                response_text = contract_address_error
            elif ifOwner != True:
                response_text = "You are not the owner of this group"
            else:
                try:
                    with open('examples.json', 'r') as file:
                        data = json.load(file)
                        new_value = {"contractAddress": contract_address, "groupID": chat_id, "isActive": 1, "owner": group_owner, "password": random_password}
                        value_exists = False
                        value_exists = any(value == new_value or (value['contractAddress'] == new_value['contractAddress'] and value['isActive'] == 1) for value in data.values())
                        if not value_exists:
                            new_key = str(len(data) + 1)
                            data[new_key] = new_value
                            try:
                                with open('examples.json', 'w') as file:
                                    json.dump(data, file)
                                    response_text = "Added"
                            except Exception as e:
                                line_number = sys._getframe().f_lineno
                                response_text = "Error: {} on line {}".format(e, line_number)
                                logger.error(response_text)
                        else:
                            response_text = "Already exists"
                except Exception as e:
                    line_number = sys._getframe().f_lineno
                    response_text = "Error: {} on line {}".format(e, line_number)
                    logger.error(response_text)
        else:
            response_text = "There is a missing parameter."
    await sendMessage(chat_id, response_text, _bot)
async def sendDocument(chat_id, document, _bot):
    try:
        async with _bot:
            await _bot.send_document(chat_id=chat_id, document=document)
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def sendReplyDocument(chat_id, document, message_id, _bot):
    try:
        async with _bot:
            await _bot.send_document(chat_id=chat_id, document=document, reply_to_message_id=message_id)
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def getChatAdministrators(chat_id, _sender, _bot):
    try:
        async with _bot:
            result = await _bot.get_chat_administrators(chat_id=chat_id)
            if str(_sender) in str(result):
                return True
            else:
                return False
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def sendMessageWithParseMode(chat_id, text: str, _bot, _parse_mode):
    try:
        async with _bot:
            await _bot.send_message(chat_id=chat_id, text=text, parse_mode=_parse_mode)
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def sendMessageWithDisableWebPagePreview(chat_id, text: str, _bot):
    try:
        async with _bot:
            await _bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def sendMessage(chat_id, text: str, _bot):
    try:
        async with _bot:
            await _bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def sendMessageWithReturn(chat_id, text: str, _bot):
    result = None
    try:
        async with _bot:
            result = await _bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        async with _bot:
            result = await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
    return result
async def sendKeyboardMarkup(chat_id, text: str, _bot, _type):
    try:
        async with _bot:
            await _bot.send_message(chat_id=chat_id, text=text, reply_markup=_type)
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def sendReplyAPIKwargs(chat_id, text: str, _bot, _type):
    try:
        async with _bot:
            await _bot.send_message(chat_id=chat_id, text=text, api_kwargs=_type)
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def getUserName(chat_id, userID, _bot):
    try:
        async with _bot:
            return await _bot.get_chat_member(chat_id=chat_id, user_id=userID)
    except Exception as e:
        async with _bot:
            if 'User not found' in str(e):
                return None          
async def replyMessage(chat_id, text: str, message_id, _bot):
    try:
        async with _bot:
            await _bot.send_message(chat_id=chat_id, text=text, reply_to_message_id=message_id)
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))
async def deleteMessage(chat_id, message_id, _bot):
    try:
        async with _bot:
            await _bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        async with _bot:
            await _bot.sendMessage(chat_id=chat_id, text='Error: {}'.format(e))

def handle_logger(log_path, type):
    today = time.strftime("%Y-%m-%d")
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger('my_logger')
    rootLogger = logging.getLogger()
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    handler = logging.handlers.TimedRotatingFileHandler(
        f"{log_path}/{type}-{today}-log.log", when="midnight", backupCount=7
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(logFormatter)
    logger.addHandler(handler)
    return logger