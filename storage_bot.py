import sqlite3, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- কনফিগারেশন (আপনার দেওয়া তথ্য অনুযায়ী) ---
TOKEN = '8381028873:AAFdyO9DWYPNZ2w4rT3DliOPkR_uyM8ignA'
CHANNEL_ID = -1003802624784 
ADMIN_LIST = [8590783774, 8153774922] 
BOT_USERNAME = 'PBDDemo69_bot' 
DB_PATH = 'batch_storage.db'

# ডাটাবেজ সেটআপ
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS batches (id INTEGER PRIMARY KEY AUTOINCREMENT, file_ids TEXT)')
    conn.commit(); conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
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
                    # ফাইল কপি হবে ইউজারের ইনবক্সে
                    m = await context.bot.copy_message(chat_id=user_id, from_chat_id=CHANNEL_ID, message_id=int(f_id))
                    sent_msgs.append(m.message_id)
                except: pass
            
            # ৩০ মিনিট ডিলিট সতর্কবার্তা
            warn = await update.message.reply_text(
                "⌛ <b>This content is available for 30 minutes!</b>\nSave & Download now to keep it forever!", 
                parse_mode=ParseMode.HTML
            )
            
            # ৩০ মিনিট পর ইনবক্স থেকে ডিলিট করার প্রসেস
            await asyncio.sleep(1800) 
            for m_id in sent_msgs:
                try: await context.bot.delete_message(user_id, m_id)
                except: pass
            # কপিরাইট সতর্কবার্তা
            try: await warn.edit_text("❌ <b>Files deleted for copyright.</b>\nপুনরায় দেখতে একই লিঙ্ক ব্যবহার করুন।", parse_mode=ParseMode.HTML)
            except: pass
            return

    await update.message.reply_text("👋 <b>Welcome!</b> ফাইল স্টোর করতে <b>Menu</b> ব্যবহার করুন।", parse_mode=ParseMode.HTML)

# ব্যাচ তৈরির সিস্টেম
user_batches = {}

async def make_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_LIST:
        user_batches[update.effective_user.id] = []
        await update.message.reply_text("📤 <b>Send files now...</b>", parse_mode=ParseMode.HTML)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_batches:
        msg = await update.message.copy(CHANNEL_ID)
        user_batches[uid].append(msg.message_id)
        await update.message.reply_text(f"📦 <b>Files added: {len(user_batches[uid])}</b>", parse_mode=ParseMode.HTML)

async def make_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_batches and user_batches[uid]:
        ids_str = ",".join(map(str, user_batches[uid]))
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute('INSERT INTO batches (file_ids) VALUES (?)', (ids_str,))
        db_id = cur.lastrowid; conn.commit(); conn.close()
        await update.message.reply_text(f"🔗 <b>Link:</b> <code>https://t.me/{BOT_USERNAME}?start={db_id}</code>", parse_mode=ParseMode.HTML)
        del user_batches[uid]

# মেইন ফাংশন (Railway-র এরর সমাধানের জন্য সংশোধিত)
async def post_init(application: Application):
    commands = [
        BotCommand("start", "Restart the bot 🤖"),
        BotCommand("make_files", "Send & Make File 📂"),
        BotCommand("make_link", "Make file link 🔗")
    ]
    await application.bot.set_my_commands(commands)

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
