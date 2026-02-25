import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- কনফিগারেশন ---
TOKEN = '8721328509:AAGResWlCB3Sjm3YdgsyvG4hKT2QuSuimDo' 
ADMIN_LIST = [8590783774, 8153774922]
CHANNEL_ID = -1003802624784 
DB_PATH = 'storage.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, msg_id INTEGER)')
    conn.commit()
    conn.close()

# ডেমো ওপেন করার জন্য
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        file_id = context.args[0]
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute('SELECT msg_id FROM files WHERE id = ?', (file_id,))
        res = cur.fetchone(); conn.close()
        if res:
            try:
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id, from_chat_id=CHANNEL_ID,
                    message_id=res[0], caption="🎬 <b>Exclusive Demo Preview</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Buy Premium 💸", url="https://t.me/PBDDemo69_bot")]])
                )
            except:
                await update.message.reply_text("❌ ফাইলটি স্টোরেজে নেই।")
            return
    await update.message.reply_text("💎 <b>Premium Plans:</b>\n\n১ মাস - ৪৫০ TK\n৩ মাস - ১২০০ TK")

# লিঙ্ক জেনারেট করার জন্য
async def handle_admin_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_LIST: return
    msg = update.message
    file = msg.video or msg.document or (msg.photo[-1] if msg.photo else None)
    if not file: return

    status = await msg.reply_text("⌛ <i>Generating Link...</i>")
    try:
        c_msg = await context.bot.copy_message(chat_id=CHANNEL_ID, from_chat_id=msg.chat_id, message_id=msg.message_id)
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute('INSERT INTO files (msg_id) VALUES (?)', (c_msg.message_id,))
        db_id = cur.lastrowid; conn.commit(); conn.close()
        
        link = f"https://t.me/PBDDemo69_bot?start={db_id}"
        await status.edit_text(f"✅ <b>Link Generated!</b>\n\n<code>{link}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await status.edit_text(f"❌ Error: {e}")

async def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_admin_files))
    print("✅ Storage Bot is Running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(10)

if __name__ == '__main__':
    asyncio.run(main())
