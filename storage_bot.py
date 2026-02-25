import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- কনফিগারেশন (আপনার দেওয়া তথ্য অনুযায়ী) ---
TOKEN = '8721328509:AAGResWlCB3Sjm3YdgsyvG4hKT2QuSuimDo' 
ADMIN_LIST = [8590783774, 8153774922]
CHANNEL_ID = -1003802624784 
DB_PATH = 'storage_bot.db'

# ডাটাবেজ সেটআপ
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, msg_id INTEGER)')
    conn.commit()
    conn.close()

# স্টার্ট কমান্ড: ইউজারদের ডেমো ভিডিও দেখাবে
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        file_id = context.args[0]
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute('SELECT msg_id FROM files WHERE id = ?', (file_id,))
        result = cursor.fetchone(); conn.close()
        
        if result:
            msg_id = result[0]
            caption = "🎬 <b>Exclusive Demo Preview</b>\n\n✅ সম্পূর্ণ ভিডিও এবং ডেইলি আপডেট পেতে সাবস্ক্রিপশন নিন।"
            keyboard = [[InlineKeyboardButton("Buy Premium Subscription 💸", url="https://t.me/PBDDemo69_bot")]]
            try:
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id, from_chat_id=CHANNEL_ID,
                    message_id=msg_id, caption=caption, parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except:
                await update.message.reply_text("❌ দুঃখিত, ফাইলটি স্টোরেজে নেই।")
            return

    await update.message.reply_text("💎 <b>Premium Subscription Plans:</b>\n\n১ মাস - ৪৫০ TK\n৩ মাস - ১২০০ TK")

# ফাইল হ্যান্ডলার: অ্যাডমিন ভিডিও পাঠালে এই বটই লিঙ্ক জেনারেট করবে
async def handle_admin_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_LIST: return
    
    msg = update.message
    # ভিডিও বা ফাইল ডিটেক্ট করা
    file = msg.video or msg.document or (msg.photo[-1] if msg.photo else None)
    if not file: return

    status = await msg.reply_text("⌛ <i>Generating your Demo Link...</i>")
    
    try:
        # স্টোরেজ চ্যানেলে কপি করে পাঠানো
        c_msg = await context.bot.copy_message(chat_id=CHANNEL_ID, from_chat_id=msg.chat_id, message_id=msg.message_id)
        
        # ডিবিতে লিঙ্ক সেভ করা
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute('INSERT INTO files (msg_id) VALUES (?)', (c_msg.message_id,))
        db_id = cursor.lastrowid; conn.commit(); conn.close()
        
        # এই বটের ইউজারনেম দিয়ে লিঙ্ক তৈরি
        link = f"https://t.me/PBDDemo69_bot?start={db_id}"
        
        await status.edit_text(
            f"✅ <b>সফলভাবে লিঙ্ক তৈরি হয়েছে!</b>\n\n"
            f"🔗 <b>লিঙ্ক:</b> <code>{link}</code>\n\n"
            f"এই লিঙ্কটি এখন আপনার মেইন চ্যানেলে পোস্ট করতে পারেন।",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await status.edit_text(f"❌ Error: {e}")

async def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_admin_files))
    
    print("✅ Storage Bot is Live...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True: await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
