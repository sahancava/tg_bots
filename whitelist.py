import sys
import os
import flask
import threading
# from flask import Flask, request, jsonify
# import asyncio
from quart import Quart, request, jsonify
import telegram 
from helpers import (create_mysql_connection, sendMessage, handle_config)

BOT_TOKEN, BOT_CREATOR_ID, LOG_PATH, TELEGRAM_API_BASE_URL, WEBHOOK_URL, WHITELIST_TOKEN = handle_config()

app = Quart(__name__)
bot = telegram.Bot(token=WHITELIST_TOKEN)

@app.route('/whitelist', methods=['POST'])
async def webhook():
    data = await request.get_json()
    try:
        if 'message' in data:
            if 'text' in data['message']:
                message = data['message']['text']
                if message.startswith('/addWhitelist') and data['message']['chat']['type'] == 'private' and data['message']['from']['is_bot'] == False:
                    await handle_whitelist(data, bot)
    except Exception as e:
        print(e)

    return jsonify({"whitelist": True}), 200

async def handle_whitelist(data, bot):
    chat_id = data['message']['chat']['id']
    message = data['message']['text']

    cnx = await create_mysql_connection()
    cursor = cnx.cursor()
    query = "SELECT * FROM whitelist_campaigns where group_id = %s"
    await cursor.execute(query, (chat_id,))
    result = await cursor.fetchall()
    if len(result) == 0:
        query = "INSERT INTO whitelist_registrations (campaign_id, chat_id, chat_title, tier) VALUES (1, %s, %s, 1)"
        await cursor.execute(query, (chat_id, message))
        await cnx.commit()
        await sendMessage(chat_id, "Inserted", bot)
    else:
        await sendMessage(chat_id, "Already whitelisted", bot)
    cursor.close()
    cnx.close()

if __name__ == '__main__':
    app.run(debug=True, port=8443)
