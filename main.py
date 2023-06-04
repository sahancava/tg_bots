import asyncio
import logging
import os
import random
import uuid
import logging.handlers
import telegram
from multiprocessing import Process
import glob
import csv
import threading
from datetime import datetime, timedelta
import flask
import sys
import pyminizip
from itertools import groupby
from flask import Flask, request
import json
from decimal import Decimal

import time
from helpers import (
    handle_help_command,
    removeLogFiles,
    create_mysql_connection,
    replyMessage,
    getUserName,
    sendMessage,
    getChatAdministrators,
    sendReplyDocument,
    sendDocument,
    handle_add_another_command,
    handle_logger,
    handle_config
)
BOT_TOKEN, BOT_CREATOR_ID, LOG_PATH, TELEGRAM_API_BASE_URL, WEBHOOK_URL, WHITELIST_TOKEN, PRESALE_TOKEN = handle_config()
app = Flask(__name__)

bot = telegram.Bot(token=BOT_TOKEN)

logger = handle_logger(LOG_PATH, 'statistics')

@app.route('/{}'.format(WEBHOOK_URL), methods=['POST', 'GET'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if request.method == 'POST':
        data = request.json
        try:
            if 'message' in data:
                if 'text' in data['message']:
                    message = data['message']['text']
                    chat_id = data['message']['chat']['id']
                    sender = data['message']['from']['id']
                    if 'group' in data['message']['chat']['type']:
                        ifOwner = asyncio.run(getChatAdministrators(chat_id, int(sender), bot))

                        if message.startswith('/addProject') and data['message']['from']['is_bot'] == False:
                            if ifOwner != True:
                                asyncio.run(sendMessage(chat_id, "You are not allowed to add", bot))
                            else:
                                asyncio.run(handle_add_another_command(data, bot, logger))
                        elif message.startswith('/removeProject') and data['message']['from']['is_bot'] == False:
                            if ifOwner != True:
                                asyncio.run(sendMessage(chat_id, "You are not allowed to remove a project!", bot))
                            else:
                                try:
                                    chat_message = data['message']['text']
                                    split_message = chat_message.split()
                                    if len(split_message) == 2:
                                        removeProject = split_message[1]
                                        if len(removeProject) < 1:
                                            asyncio.run(sendMessage(chat_id, "Please provide a contract address to add", bot))
                                        elif len(removeProject) > 0 and len(removeProject) < 42:
                                            asyncio.run(sendMessage(chat_id, "Invalid contract address", bot))
                                        elif len(removeProject) == 42 and removeProject.startswith("0x"):
                                            with open('examples.json', 'r') as file:
                                                data = json.load(file)
                                                values_removed = []
                                                for value in data.values():
                                                    if value['contractAddress'] == removeProject and value['isActive'] == 1:
                                                        value['isActive'] = 0
                                                        values_removed.append(value['contractAddress'])
                                                with open('examples.json', 'w') as file:
                                                    json.dump(data, file)
                                                    if values_removed:
                                                        response_text = f"Removed the following values: {', '.join(values_removed)}"
                                                    else:
                                                        response_text = "No matching values found"
                                                    asyncio.run(sendMessage(chat_id, response_text, bot))
                                        else:
                                            asyncio.run(sendMessage(chat_id, "Invalid contract address", bot))
                                    else:
                                        asyncio.run(sendMessage(chat_id, "No contract address provided", bot))
                                except Exception as e:
                                    line_number = sys._getframe().f_lineno
                                    something_went_wrong = "Something went wrong: {} on line {}".format(e, line_number)
                                    logger.error(something_went_wrong)
                        elif message.startswith('/checkParticipants') and data['message']['from']['is_bot'] == False:
                            try:
                                cnx = create_mysql_connection()
                                cursor = cnx.cursor()
                                query = 'SELECT * FROM records order by startingHour desc'
                                cursor.execute(query)
                                row = cursor.fetchall()
                                if row != [] and row is not None:
                                    row.sort(key=lambda x: x[3], reverse=True)
                                    groups = groupby(row, key=lambda x: x[3].strftime('%Y-%m-%d %H:%M:%S'))
                                    text_message = ""
                                    text_message += "Date and Time (UTC) | Participants\n"
                                    for key, group in groups:
                                        items = list(group)
                                        text_message += key + " | " + str(len(items)) + "\n"
                                asyncio.run(sendMessage(chat_id, text_message, bot))
                                cnx.close()
                                logger.info("Successfully checked participants")
                            except Exception as e:
                                line_number = sys._getframe().f_lineno
                                something_went_wrong = "Something went wrong: {} on line {}".format(e, line_number)
                                logger.error(something_went_wrong)
                        elif message.startswith('/downloadWinners') and data['message']['from']['is_bot'] == False:
                            whatGroupID = None
                            whatContractAddress = None
                            value_exists = False
                            filePassword = None
                            if ifOwner:
                                try:
                                    with open('examples.json', 'r') as file:
                                        loadedData = json.load(file)
                                        for value in loadedData.values():
                                            if value['owner'] == int(sender) and value['isActive'] == 1:
                                                value_exists = True
                                                whatGroupID = value['groupID']
                                                whatContractAddress = value['contractAddress']
                                                filePassword = value['password']
                                                break
                                    if value_exists and whatGroupID is not None:
                                        text_message = ""
                                        try:
                                            contains = False
                                            current_time = datetime.now().replace(minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
                                            cnx = create_mysql_connection()
                                            cursor = cnx.cursor()
                                            cursor2 = cnx.cursor()
                                            query2 = 'SELECT * FROM winners where isPaid = 0 and groupID = {} order by ID desc'.format(whatGroupID)
                                            cursor.execute(query2)
                                            row = cursor.fetchall()
                                            try:
                                                cursor2.execute(query2)
                                                row2 = cursor2.fetchall()
                                                if row2 != [] and row2 is not None:
                                                    row2.sort(key=lambda x: x[2], reverse=False)
                                                    fp = open(whatContractAddress+'.csv', 'w')
                                                    myFile = csv.writer(fp)
                                                    for item in row:
                                                        userName = asyncio.run(getUserName(chat_id, item[1], bot))['user']['username']
                                                        myFile.writerow([item[2], ' @'+userName])
                                                    fp.close()
                                                    input = whatContractAddress+'.csv'
                                                    pre = None
                                                    output = whatContractAddress+'.zip'
                                                    compress_level = 5
                                                    try:
                                                        pyminizip.compress(input, pre, output, str(filePassword), compress_level)
                                                        asyncio.run(sendReplyDocument(chat_id, whatContractAddress+'.zip', data['message']['message_id'], bot))
                                                        os.remove(whatContractAddress+'.csv')
                                                        os.remove(whatContractAddress+'.zip')
                                                        contains = True
                                                        text_message = "Winners downloaded"
                                                    except Exception as e:
                                                        line_number = sys._getframe().f_lineno
                                                        response_text = "Error: {} on line {}".format(e, line_number)
                                                        logger.error(response_text)
                                                if contains:
                                                    try:
                                                        string = 'UPDATE winners SET isPaid = 1 WHERE groupID = {}'.format(whatGroupID)
                                                        cursor.execute(string)
                                                        cnx.commit()
                                                        cursor.close()
                                                        cnx.close()
                                                    except Exception as e:
                                                        line_number = sys._getframe().f_lineno
                                                        response_text = "SQL Error: {} on line {}".format(e, line_number)
                                                        logger.error(response_text)
                                                else:
                                                    text_message = "No winners found"
                                                asyncio.run(replyMessage(chat_id, text_message, data['message']['message_id'], bot))
                                            except Exception as err:
                                                line_number = sys._getframe().f_lineno
                                                something_went_wrong = "Error: {} on line {}".format(str(err), str(line_number))
                                                logger.error(something_went_wrong)
                                        except Exception as e:
                                            line_number = sys._getframe().f_lineno
                                            something_went_wrong = "Error: {} on line {}".format(str(e), str(line_number))
                                            logger.error(something_went_wrong)
                                except Exception as e:
                                    line_number = sys._getframe().f_lineno
                                    something_went_wrong = "Error: {} on line {}".format(str(e), str(line_number))
                                    logger.error(something_went_wrong)
                            else:
                                asyncio.run(sendMessage(chat_id, "You are not the owner of this group", bot))
                        elif message.startswith('/checkWinners') and data['message']['from']['is_bot'] == False:
                            try:
                                cnx = create_mysql_connection()
                                cursor = cnx.cursor()
                                query = 'SELECT * FROM winners order by ID desc limit 5'
                                cursor.execute(query)
                                row = cursor.fetchall()
                                if row != [] and row is not None:
                                    row.sort(key=lambda x: x[2], reverse=False)
                                    text_message = ""
                                    text_message += "Date and Time (UTC) | Winner\n"
                                    for item in row:
                                        result = asyncio.run(getUserName(chat_id, item[1], bot))
                                        user = result['user']['username'] if result and result['user'] and result['user']['username'] else None
                                        if user is not None:
                                            time = item[2].strftime('%Y-%m-%d %H:%M:%S')
                                            text_message += time + " | @" + user + "\n"
                                asyncio.run(sendMessage(chat_id, text_message, bot))
                                cnx.close()
                            except Exception as e:
                                line_number = sys._getframe().f_lineno
                                something_went_wrong = "Error: {} on line {}".format(str(e), str(line_number))
                                logger.error(something_went_wrong)
                        else:
                            if data['message']['from']['is_bot'] == False:
                                with open('examples.json', 'r') as file:
                                    loadedData = json.load(file)
                                    value_exists = False
                                    for value in loadedData.values():
                                        if value['groupID'] == int(chat_id) and value['isActive'] == 1:
                                            value_exists = True
                                            break
                                    if value_exists:
                                        try:
                                            response_text = None
                                            cnx = create_mysql_connection()
                                            cursor = cnx.cursor()
                                            current_time = datetime.now().replace(minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
                                            query = 'SELECT * FROM records WHERE UserID = ' + '"' + str(data['message']['from']['id']) + '" AND startingHour = ' + '"' + current_time + '"'
                                            cursor.execute(query)
                                            row = cursor.fetchone()

                                            cursor2 = cnx.cursor()
                                            query2 = 'SELECT * FROM records WHERE startingHour != ' + '"' + str(current_time) + '" and isProcessed = 0'
                                            cursor2.execute(query2)
                                            row2 = cursor2.fetchall()

                                            cursor2.close()

                                            if row2 != [] and row2 is not None:
                                                cursor3 = cnx.cursor()
                                                row2.sort(key=lambda x: x[3])
                                                groups = groupby(row2, key=lambda x: x[3].strftime('%Y-%m-%d %H:%M:%S'))
                                                for key, group in groups:
                                                    items = list(group)
                                                    random_item = random.choice(items)
                                                    cursor3.execute('UPDATE records SET isProcessed = 1 WHERE startingHour = ' + '"' + str(key) + '"')
                                                    insert_string = "INSERT INTO winners (UserID, winDate, groupID) VALUES ('" + str(random_item[1]) + "', '" + str(key) + "', " + str(data['message']['chat']['id']) + ")"
                                                    cursor3.execute(insert_string)
                                                    cnx.commit()

                                            if row != [] and row is not None:
                                                recorded_message_count = row[2] + 1
                                                cursor.execute("UPDATE records SET recordedMessageCount = " + str(recorded_message_count) + " WHERE ID = " + str(row[0]))
                                                cnx.commit()
                                            else:
                                                userName = asyncio.run(getUserName(chat_id, data['message']['from']['id'], bot))['user']['username']
                                                string = "INSERT INTO records (UserID, recordedMessageCount, startingHour, isProcessed, groupID, userName) VALUES ('" + (str(data['message']['from']['id']) + "', 1, '" + current_time + "', 0, " + str(data['message']['chat']['id']) + ", '" + str(userName) + "')")
                                                cursor.execute("INSERT INTO records (UserID, recordedMessageCount, startingHour, isProcessed, groupID, userName) VALUES ('" + (str(data['message']['from']['id']) + "', 1, '" + current_time + "', 0, " + str(data['message']['chat']['id']) + ", '" + str(userName) + "')"))
                                                cnx.commit()
                                            cursor.close()
                                            cnx.close()
                                            logger.info("Message got from user: %s", str(data['message']['from']['id']))
                                            if response_text is not None:
                                                asyncio.run(sendMessage(chat_id, response_text, bot))
                                        except Exception as err:
                                            line_number = sys._getframe().f_lineno
                                            logger.error("Error occurred while connecting to the database: %s at line %s", str(err), str(line_number))
                                            response_text = "Oops! Something went wrong. Please try again later."
                                    else:
                                        asyncio.run(sendMessage(chat_id, 'This groupID is not allowed to use this bot', bot))
                    elif (message == '/help' or message == 'help') and data['message']['chat']['type'] == 'private':
                        asyncio.run(handle_help_command(data, bot, BOT_CREATOR_ID, logger=logger))
                    elif data['message']['chat']['type'] == 'private':
                        if int(BOT_CREATOR_ID) == int(data['message']['from']['id']):
                            if message.startswith('/downloadLogFile'):
                                split_message = data['message']['text'].split()
                                if len(split_message) == 2:
                                    whichLogFile = split_message[1]
                                    if len(whichLogFile) < 1 and type(whichLogFile) != int:
                                        asyncio.run(sendMessage(chat_id, "Please provide a parameter for the command. Usage: /downloadLogFile 15", bot))
                                    else:
                                        list_of_files = glob.glob('logs/*.log')
                                        latest_file = sorted(list_of_files, key=os.path.getctime)
                                        asyncio.run(sendDocument(chat_id, latest_file[-int(whichLogFile)], bot))
                                else:
                                    asyncio.run(sendMessage(chat_id, "Please provide a parameter for the command.\nUsage:\n/downloadLogFile 15", bot))
                            if message.startswith('/removeLogFiles'):
                                asyncio.run(removeLogFiles(chat_id, bot, logger))
                        elif message.startswith('/myPasswords'):
                            try:
                                value_exists = False
                                with open('examples.json', 'r') as file:
                                    loadedData = json.load(file)
                                    for value in loadedData.values():
                                        if str(value['owner']) == str(sender) and value['isActive'] == 1:
                                            value_exists = True
                                            result_string = 'Contract Address | Password\n'
                                            result_string += '-----------------------------\n'
                                            result_string += str(value['contractAddress']) + ' | ' + str(value['password'])
                                            asyncio.run(sendMessage(chat_id, result_string, bot))
                            except Exception as err:
                                line_number = sys._getframe().f_lineno
                                logger.error("Error occurred while reading examples.json: %s at line %s", str(err), str(line_number))
                    return 'OK'
                else:
                    return 'OK'
            raise Exception('Invalid JSON')
        except Exception as e:
            line_number = sys._getframe().f_lineno
            logger.error("Error occurred while handling webhook: %s at line %s", str(e), str(line_number))
            result = flask.jsonify({'status': 'error', 'error': str(e)})
            return result, 500
    result = flask.jsonify({'status': 'ok'})
    return result, 200

async def main():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run(debug=True, port=8443, threaded=True)
    loop.close()

if __name__ == '__main__':
    asyncio.run(main())
