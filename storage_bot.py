import sqlite3, asyncio, os, base64
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

# লিঙ্ক বড় করার এনকোডিং ফাংশন
def encode_id(db_id):
    text = f"get-{db_id}-alpha-premium-secure-storage-69"
    return base64.urlsafe_b64encode(text.encode()).decode().replace("=", "")

def decode_id(encoded_str):
    try:
        padding = "=" * (4 - len(encoded_str) % 4)
        decoded_text = base64.urlsafe_b64decode(encoded_str + padding).decode()
        return decoded_text.split("-")[1]
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # লিঙ্ক থেকে ফাইল ডেলিভারি
    if context.args:
        db_id = decode_id(context.args[0])
        if not db_id:
            await update.message.reply_text("❌ <b>Invalid Link!</b>", parse_mode=ParseMode.HTML)
            return

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
            
            warn = await update.message.reply_text("⌛ <b>This content is available for 30 minutes!</b>", parse_mode=ParseMode.HTML)
            
            await asyncio.sleep(1800) # ৩০ মিনিট
            for m_id in sent_msgs:
                try: await context.bot.delete_message(user_id, m_id)
                except: pass
            try: await warn.edit_text("❌ <b>Files deleted to avoid copyright infringement.</b>", parse_mode=ParseMode.HTML)
            except: pass
            return

    # --- আলফা প্রিমিয়াম ওয়েলকাম টেক্সট ---
    welcome_text = (
        "👋 <b>Welcome to Drive File-Store Bot!</b>\n\n"
        "📢 <b>Powered by:</b> <a href='https://t.me/Alpha_Premium_B'>Alpha Premium</a>\n\n"
        "📤 Send me any video, photo, or document\n"
        "🔗 I will instantly convert it into a shareable link\n\n"
        "1️⃣ Send /make_files to start a batch\n"
        "2️⃣ Send files and click 'Create Secure Link'"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Alpha Premium", url="https://t.me/Alpha_Premium_B")]
    ])
    
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML, reply_markup=keyboard, disable_web_page_preview=True)

# --- ব্যাচ সিস্টেম ---
user_data = {}

async def make_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_LIST: return
    user_data[update.effective_user.id] = {'files': [], 'status_msg': None}
    await update.message.reply_text("📤 <b>Batch Started!</b>\nএখন আপনার ফাইলগুলো একে একে পাঠান।")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_data:
        msg = await update.message.copy(CHANNEL_ID)
        user_data[uid]['files'].append(msg.message_id)
        
        count = len(user_data[uid]['files'])
        text = f"📦 <b>Files added: {count}</b>\n\nসব পাঠানো শেষ হলে নিচের বাটনে ক্লিক করুন।"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Create Alpha Secure Link", callback_data="gen_link")]])
        
        if user_data[uid]['status_msg'] is None:
            user_data[uid]['status_msg'] = await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            try: await user_data[uid]['status_msg'].edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            except: pass

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    
    if query.data == "gen_link" and uid in user_data:
        if not user_data[uid]['files']:
            await query.answer("আগে ফাইল পাঠান!", show_alert=True)
            return
            
        ids_str = ",".join(map(str, user_data[uid]['files']))
        conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
        cur.execute('INSERT INTO batches (file_ids) VALUES (?)', (ids_str,))
        db_id = cur.lastrowid; conn.commit(); conn.close()
        
        long_id = encode_id(db_id)
        link = f"https://t.me/{BOT_USERNAME}?start={long_id}"
        
        await query.edit_message_text(
            f"✅ <b>Success!</b>\nআপনার {len(user_data[uid]['files'])}টি ফাইলের এনক্রিপ্টেড লিঙ্ক:\n\n<code>{link}</code>", 
            parse_mode=ParseMode.HTML
        )
        del user_data[uid]

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Restart the bot 🤖"),
        BotCommand("make_files", "Start Batch 📂")
    ])

def main():
    init_db()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("make_files", make_files))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_media))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("✅ Alpha Premium Bot is Online!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
