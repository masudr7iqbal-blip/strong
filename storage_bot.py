import sqlite3, asyncio
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- কনফিগারেশন ---
TOKEN = '8381028873:AAFdyO9DWYPNZ2w4rT3DliOPkR_uyM8ignA'
CHANNEL_ID = -1003802624784 
ADMIN_LIST = [8590783774, 8153774922] 
BOT_USERNAME = 'PBDDemo69_bot' 
DB_PATH = 'batch_storage.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS batches (id INTEGER PRIMARY KEY AUTOINCREMENT, file_ids TEXT)')
    conn.commit(); conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # যদি ইউজার কোনো লিঙ্কে ক্লিক করে আসে (start parameter থাকলে)
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
                    m = await context.bot.copy_message(chat_id=user_id, from_chat_id=CHANNEL_ID, message_id=int(f_id))
                    sent_msgs.append(m.message_id)
                except: pass
            
            # ৩০ মিনিটের সতর্কবার্তা
            warn = await update.message.reply_text(
                "⌛ <b>This content is available for 30 minutes!</b>\nSave & Download now to keep it forever! 🔥", 
                parse_mode=ParseMode.HTML
            )
            
            # ৩০ মিনিট পর ইনবক্স থেকে অটো ডিলিট
            await asyncio.sleep(1800) 
            for m_id in sent_msgs:
                try: await context.bot.delete_message(user_id, m_id)
                except: pass
            
            # ফাইল ডিলিট হওয়ার পর মেসেজ আপডেট
            try:
                await warn.edit_text("❌ <b>Your files have been deleted to avoid copyright infringement.</b>\nআপনি চাইলে আগের লিঙ্ক থেকে পুনরায় ফাইলটি দেখতে পারবেন।", parse_mode=ParseMode.HTML)
            except: pass
            return

    # সাধারণ /start বা Restart দিলে এই Welcome Text দেখাবে
    welcome_text = (
        "👋 <b>Welcome to Drive File-Store Bot!</b>\n\n"
        "📤 Send me any video, photo, or document\n"
        "🔗 I will instantly convert it into a shareable link\n\n"
        "1️⃣ Send /make_files video, photo, or document\n"
        "2️⃣ When finished, send /make_link to receive your shareable link."
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

# --- ব্যাচ ফাইল তৈরির ফাংশনসমূহ ---
user_batches = {}

async def make_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_LIST:
        user_batches[update.effective_user.id] = []
        await update.message.reply_text("📤 <b>Send your files now</b>\n\n• Videos / Photos / Documents\n• Albums supported\n\n➡️ Send /make_link when finished", parse_mode=ParseMode.HTML)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_batches:
        msg = await update.message.copy(CHANNEL_ID)
        user_batches[uid].append(msg.message_id)
        # ফাইল কাউন্ট দেখানো
        await update.message.reply_text(
            f"📦 <b>Files added: {len(user_batches[uid])}</b>\n📌 <b>Batch in progress</b>\n\n• Send more files to continue\n• Use /make_link to create a shareable link", 
            parse_mode=ParseMode.HTML
        )

async def make_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_batches and user_batches[uid]:
        ids_str = ",".join(map(str, user_batches[uid]))
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute('INSERT INTO batches (file_ids) VALUES (?)', (ids_str,))
        db_id = cur.lastrowid; conn.commit(); conn.close()
        
        link = f"https://t.me/{BOT_USERNAME}?start={db_id}"
        kb = [[InlineKeyboardButton("🚀 Share URL", url=f"https://t.me/share/url?url={link}")]]
        await update.message.reply_text(
            f"🔗 <b>Your shareable link is ready!</b>\n\n{link}", 
            parse_mode=ParseMode.HTML, 
            reply_markup=InlineKeyboardMarkup(kb)
        )
        del user_batches[uid]
    else:
        await update.message.reply_text("❌ <b>No files found!</b>", parse_mode=ParseMode.HTML)

# --- রেলওয়ে এরর ফিক্স এবং স্টার্ট ---
async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Restart the bot 🤖"),
        BotCommand("make_files", "Send & Make File 📂"),
        BotCommand("make_link", "Make file link 🔗")
    ])

def main():
    init_db()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("make_files", make_files))
    app.add_handler(CommandHandler("make_link", make_link))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_media))
    
    print("✅ Bot is online...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
