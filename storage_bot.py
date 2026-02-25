import sqlite3
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- কনফিগারেশন ---
TOKEN = '8721328509:AAGResWlCB3Sjm3YdgsyvG4hKT2QuSuimDo' # @PBDDemo69_bot
ADMIN_LIST = [8590783774, 8153774922]
CHANNEL_ID = -1003802624784 
DB_PATH = 'storage_data.db'

# ডাটাবেজ সেটআপ
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, msg_id INTEGER)')
    conn.commit()
    conn.close()

# স্টার্ট কমান্ড: ইউজারদের জন্য ফাইল ওপেন করবে
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        file_id = context.args[0]
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute('SELECT name, msg_id FROM files WHERE id = ?', (file_id,))
        result = cursor.fetchone(); conn.close()
        
        if result:
            name, msg_id = result
            caption = f"🎬 <b>Preview: {name}</b>\n\n✅ সম্পূর্ণ ভিডিও পেতে সাবস্ক্রিপশন নিন।"
            keyboard = [[InlineKeyboardButton("Buy Premium Subscription 💸", url="https://t.me/PBDDemo69_bot")]]
            await context.bot.copy_message(
                chat_id=update.effective_chat.id, from_chat_id=CHANNEL_ID,
                message_id=msg_id, caption=caption, parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

    await update.message.reply_text("💎 <b>Premium Subscription Plans:</b>\n\n১ মাস - ৪৫০ TK\n৩ মাস - ১২০০ TK")

# ফাইল হ্যান্ডলার: অ্যাডমিন ফাইল পাঠালে লিঙ্ক জেনারেট করবে
async def handle_admin_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_LIST: return
    
    msg = update.message
    file = msg.document or msg.video or msg.audio or (msg.photo[-1] if msg.photo else None)
    if not file: return

    status = await msg.reply_text("⌛ <i>Generating Link...</i>", parse_mode=ParseMode.HTML)
    
    try:
        # চ্যানেলে কপি করা
        c_msg = await context.bot.copy_message(chat_id=CHANNEL_ID, from_chat_id=msg.chat_id, message_id=msg.message_id)
        
        # ডাটাবেজে সেভ
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute('INSERT INTO files (name, msg_id) VALUES (?, ?)', ("Premium Content", c_msg.message_id))
        db_id = cursor.lastrowid; conn.commit(); conn.close()
        
        # লিঙ্ক তৈরি (এই বটেরই লিঙ্ক)
        link = f"https://t.me/PBDDemo69_bot?start={db_id}"
        
        await status.edit_text(
            f"✅ <b>লিঙ্ক তৈরি হয়েছে!</b>\n\n🔗 <b>লিঙ্ক:</b> <code>{link}</code>\n\n"
            f"এই লিঙ্কটি কপি করে মেইন চ্যানেলে শেয়ার করুন।",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await status.edit_text(f"❌ Error: {e}")

async def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_admin_files))
    
    print("✅ Storage Bot is Live on Railway...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True: await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
