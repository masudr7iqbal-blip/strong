import sqlite3
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- কনফিগারেশন ---
TOKEN = '8381028873:AAFdyO9DWYPNZ2w4rT3DliOPkR_uyM8ignA'
CHANNEL_ID = -1003802624784 
DB_PATH = 'storage.db'
BOT_USERNAME = 'PBDDemo69_bot' 
ADMIN_LIST = [8590783774, 8153774922] 

# ডাটাবেজ সেটআপ
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS files 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, file_name TEXT, channel_msg_id INTEGER)''')
    conn.commit()
    conn.close()

# ৩০ মিনিট পর ডাটাবেজ থেকে মুছে ফেলার ফাংশন
async def delete_after_delay(file_db_id, delay_seconds=1800):
    await asyncio.sleep(delay_seconds)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM files WHERE id = ?', (file_db_id,))
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        file_db_id = context.args[0]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT file_name, channel_msg_id FROM files WHERE id = ?', (file_db_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            name, msg_id = result
            try:
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=CHANNEL_ID,
                    message_id=msg_id,
                    caption=f"<b>File:</b> {name}\n\n⚠️ <i>এই ফাইলটি ৩০ মিনিট পর এক্সপায়ার হয়ে যাবে।</i>",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                await update.message.reply_text("❌ <b>Error:</b> ফাইলটি পাওয়া যাচ্ছে না। বটকে চ্যানেলে Admin করুন।")
            return
        else:
            await update.message.reply_text("❌ <b>লিঙ্কটি এক্সপায়ার হয়ে গেছে!</b>", parse_mode=ParseMode.HTML)
            return

    welcome_text = (
        "👋 <b>Welcome to Drive File-Store Bot!</b>\n\n"
        "📤 অ্যাডমিন ফাইল পাঠালে আমি অটোমেটিক লিঙ্ক জেনারেট করব।\n"
        "⏱ <b>Note:</b> সব লিঙ্ক ৩০ মিনিট পর নিজে থেকেই কাজ করা বন্ধ করে দিবে।"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_LIST:
        return

    msg = update.message
    file = msg.document or msg.video or msg.audio or (msg.photo[-1] if msg.photo else None)
    if not file: return

    file_name = getattr(file, 'file_name', f"File_{msg.message_id}")
    status = await msg.reply_text("⏳ <i>Processing Admin Request...</i>", parse_mode=ParseMode.HTML)

    try:
        # চ্যানেলে কপি করা
        channel_msg = await context.bot.copy_message(
            chat_id=CHANNEL_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )
        
        # ডিবিতে সেভ
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO files (file_name, channel_msg_id) VALUES (?, ?)', 
                       (file_name, channel_msg.message_id))
        db_id = cursor.lastrowid
        conn.commit()
        conn.close()

        share_link = f"https://t.me/{BOT_USERNAME}?start={db_id}"
        keyboard = [[InlineKeyboardButton("🚀 Share Link", url=f"https://t.me/share/url?url={share_link}")]]
        
        await status.edit_text(
            f"✅ <b>File Stored Successfully!</b>\n\n📄 <b>Name:</b> <code>{file_name}</code>\n🔗 <b>Link:</b> {share_link}\n\n"
            f"⏱ <i>এই লিঙ্কটি ৩০ মিনিট পর ডিলিট হয়ে যাবে।</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # অটো ডিলিট টাস্ক রান করা
        asyncio.create_task(delete_after_delay(db_id, 1800))

    except Exception as e:
        await status.edit_text(f"❌ <b>Error:</b> {str(e)}")

async def run_bot():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_docs))
    
    print(f"Bot @{BOT_USERNAME} is Running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(10)

if __name__ == '__main__':
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass
