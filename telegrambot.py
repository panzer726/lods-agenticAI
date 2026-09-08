from telegram.ext import Application, MessageHandler, filters
import requests
from dotenv import load_dotenv
import os
load_dotenv(override=True)

TOKEN = os.getenv('telegram_api_key')
CHAT_ID = os.getenv('telegram_chat_id')

#CHAT-REPLY
async def handle_message(update, context):
    print("\nUSER:",update.message.text)

    resp = requests.post("http://localhost:8000/message", json={"source":"telegram", "content":update.message.text})
    await update.message.reply_text(resp.json()["reply"])

    print("\nAI:",resp.json()["reply"])

#REPLY ONLY
def alert_user(message):  
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": message}
    )

if __name__ == "__main__":
    print("TELEGRAM IS RUNNING")
    app = Application.builder().token(TOKEN).build()
    app.add_handler( MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message) )
    app.run_polling()