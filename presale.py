from quart import Quart, request, jsonify
from helpers import (create_mysql_connection, sendMessage, handle_config)
import telegram

BOT_TOKEN, BOT_CREATOR_ID, LOG_PATH, TELEGRAM_API_BASE_URL, WEBHOOK_URL, WHITELIST_TOKEN = handle_config()

app = Quart(__name__)
bot = telegram.Bot(token=WHITELIST_TOKEN)

@app.route('/presale', methods=['POST'])
async def webhook():
    data = await request.get_json()
    if 'message' in data:
        if 'text' in data['message']:
            message = data['message']['text']