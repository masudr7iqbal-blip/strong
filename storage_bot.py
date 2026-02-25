import sqlite3, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- কনফিগারেশন (আপনার টোকেন ও আইডি) ---
TOKEN = '8381028873:AAFdyO9DWYPNZ2w4rT3DliOPkR_uyM8ignA'
CHANNEL_ID = -1003802624784 
ADMIN_LIST = [8590783774, 8153774922] 
BOT_USERNAME = 'PBDDemo69_bot' 
DB_PATH = 'batch_storage.db'

# ডাটাবেজ সেটআপ
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    # এখানে ফাইল আইডিগুলো স্থায়ীভাবে সেভ থাকবে যাতে লিঙ্কটি বারবার কাজ করে
    cursor.execute('CREATE TABLE IF NOT EXISTS batches (id INTEGER PRIMARY KEY AUTOINCREMENT, file_ids TEXT)')
    conn.commit(); conn.close()

# মেনু কমান্ড সেটআপ
async def set_commands(application: Application):
    commands = [
        BotCommand("start", "Restart the bot 🤖"),
        BotCommand("make_files", "Send & Make File 📂"),
        BotCommand("make_link", "Make file link 🔗")
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # ইউজার সেভ করা
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit(); conn.close()

    # লিঙ্ক থেকে ফাইল রিকোয়েস্ট (ওয়ান-ক্লিক ডেলিভারি)
    if context.args:
        db_id = context.args[0]
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute('SELECT file_ids FROM batches WHERE id = ?', (db_id,))
        res = cur.fetchone(); conn.close()
        
        if res:
            file_ids = res[0].split(',')
            sent_msgs = []
            for f_id in file_ids:
                try:
                    # ফাইল চ্যানেল থেকে ইউজারের ইনবক্সে কপি হবে
                    m = await context.bot.copy_message(chat_id=user_id, from_chat_id=CHANNEL_ID, message_id=int(f_id))
                    sent_msgs.append(m.message_id)
                except: pass
            
            # সতর্কবার্তা পাঠানো (বন্ধুর বটের মতো)
            warn = await update.message.reply_text(
                "⌛ <b>This content is available for 30 minutes only!</b>\nSave & Download now to keep it forever! 🔥", 
                parse_mode=ParseMode.HTML
            )
            
            # ৩০ মিনিট পর ইনবক্স থেকে ফাইল ডিলিট করার টাস্ক
            await asyncio.sleep(1800) 
            for m_id in sent_msgs:
                try: await context.bot.delete_message(user_id, m_id)
                except: pass
            
            # সতর্কবার্তা মেসেজটি আপডেট করে কপিরাইট মেসেজ দেওয়া
            try:
                await warn.edit_text("❌ <b>Your files have been deleted to avoid copyright infringement.</b>\nআপনি চাইলে আগের লিঙ্ক থেকে পুনরায় ফাইলটি দেখতে পারেন।", parse_mode=ParseMode.HTML)
            except: pass
            return

    # সাধারণ স্টার্ট মেসেজ
    await update.message.reply_text(
        f"👋 <b>Welcome to Drive File-Store Bot!</b>\n\nফাইল পাঠিয়ে লিঙ্ক তৈরি করতে <b>Menu</b> ব্যবহার করুন।",
        parse_mode=ParseMode.HTML
    )

# ব্যাচ ফাইল তৈরি (শুধু অ্যাডমিনদের জন্য)
user_batches = {}

async def make_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_LIST: return
    user_batches[update.effective_user.id] = []
    await update.message.reply_text("📤 <b>Send your files now...</b>\n• Albums supported\n• Send /make_link when done", parse_mode=ParseMode.HTML)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_batches:
        # মেইন চ্যানেলে ফাইল স্থায়ীভাবে কপি করে রাখা
        msg = await update.message.copy(CHANNEL_ID)
        user_batches[uid].append(msg.message_id)
        await update.message.reply_text(f"📦 <b>Files added: {len(user_batches[uid])}</b>", parse_mode=ParseMode.HTML)

async def make_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_batches or not user_batches[uid]:
        await update.message.reply_text("❌ <b>No files found!</b>", parse_mode=ParseMode.HTML)
        return
    
    # ব্যাচ আইডি ডাটাবেজে সেভ করা (এটি ডিলিট হবে না)
    ids_str = ",".join(map(str, user_batches[uid]))
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute('INSERT INTO batches (file_ids) VALUES (?)', (ids_str,))
    db_id = cur.lastrowid; conn.commit(); conn.close()
    
    link = f"https://t.me/{BOT_USERNAME}?start={db_id}"
    await update.message.reply_text(f"🔗 <b>Your permanent link is ready:</b>\n\n<code>{link}</code>", parse_mode=ParseMode.HTML)
    del user_batches[uid]

async def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    await set_commands(app) # মেনু সেটআপ
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("make_files", make_files))
    app.add_handler(CommandHandler("make_link", make_link))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_media))
    
    print(f"✅ Bot @{BOT_USERNAME} is running...")
    await app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
