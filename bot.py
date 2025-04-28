import os
import json
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler


 
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_TOKEN='8046018994:AAFtjQnXG-h6SXe2Fyxu_rHpus4SsSjIdiI'
USER_DB_FILE ='./users.json'
def load_users():
    if not os.path.exists(USER_DB_FILE):
        return {}
    with open(USER_DB_FILE, "r") as f:
        return json.load(f)

# Save user data
def save_users(users):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)

# Save credentials
def save_user_credentials(user_id, username, password):
    users = load_users()
    users[str(user_id)] = {
        "username": username,
        "password": password
    }
    save_users(users)

# Get credentials
def get_user_credentials(user_id):
    users = load_users()
    return users.get(str(user_id))


async def friendly_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    greetings = ["hi", "hello", "hey", "hai", "yo", "sup"]
    if any(greet in user_text for greet in greetings):
        await update.message.reply_text("Hey there! 👋 How can I help you today?\n\nYou can press /start to begin.")


async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    greetings = ["hi", "hello", "hey", "hai", "yo", "sup"]
    if any(greet in user_text for greet in greetings):
        await friendly_reply(update, context)
    else:
        await handle_message(update, context)




async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    📋 Available Commands:
    /start - Start the bot
    /help - Show help message
    /overall - Get your Overall Attendance 📈
    /subjectwise - Get your Subject-wise Attendance 📚
    """
    await update.message.reply_text(help_text)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send your MITS credentials as: username,password.\n Example: 2369xxxxxx,YourPassword")



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Overall Attendance 📈", callback_data="overall"),
            InlineKeyboardButton("Subject-wise Attendance 📚", callback_data="subjectwise")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose an option to proceed:", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    if query.data == "overall":
        await query.edit_message_text("📡 Fetching your overall attendance...")
        # You can call the function to fetch overall attendance here
        user_id = update.callback_query.from_user.id
        creds = get_user_credentials(user_id)
        if creds:
            from main import scrape_overall_attendance
            try:
                attendance = scrape_overall_attendance(creds["username"], creds["password"])
                await query.edit_message_text(attendance)
            except Exception as e:
                await query.edit_message_text(f"⚠️ Error: {e}")
        else:
            await query.edit_message_text("❌ You haven't sent your credentials yet! Please send: username,password")

    elif query.data == "subjectwise":
        await query.edit_message_text("📡 Fetching your subject-wise attendance...")
        # You can call the function to fetch subject-wise attendance here
        user_id = update.callback_query.from_user.id
        creds = get_user_credentials(user_id)
        if creds:
            from main import scrape_subjectwise_attendance
            try:
                attendance = scrape_subjectwise_attendance(creds["username"], creds["password"])
                await query.edit_message_text(attendance)
            except Exception as e:
                await query.edit_message_text(f"⚠️ Error: {e}")
        else:
            await query.edit_message_text("❌ You haven't sent your credentials yet! Please send: username,password")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from main import scrape_attendance
    text = update.message.text
    if ',' in text:
        username, password = text.split(',', 1)
        user_id = update.message.from_user.id   # Get user's Telegram ID
        save_user_credentials(user_id, username.strip(), password.strip())
        await update.message.reply_text("📡 Fetching your attendance...")
        try:
            attendance = scrape_attendance(username.strip().upper(), password.strip())
            await update.message.reply_text(attendance)
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {e}")
    else:
        await update.message.reply_text("❌ Format incorrect! Send as: username,password")




async def subjectwise_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # First get user credentials
    from main import scrape_subjectwise_attendance
    text = update.message.text
    if ',' in text:
        username, password = text.split(',', 1)
        user_id = update.message.from_user.id   # Get user's Telegram ID
        save_user_credentials(user_id, username.strip(), password.strip())
        await update.message.reply_text("📡 Fetching your subject-wise attendance...")
        try:
            attendance = scrape_subjectwise_attendance(creds["username"], creds["password"])
            await update.message.reply_text(attendance)
        except Exception as e:
            await update.message.reply_text(f"Invalid credentials! Please send correct: username,password")
    else:
        await update.message.reply_text("❌ You haven't sent your credentials yet!\nPlease send: username,password")


async def overall_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # First get user credentials
    from main import scrape_overall_attendance
    text = update.message.text
    if ',' in text:
        username, password = text.split(',', 1)
        user_id = update.message.from_user.id   # Get user's Telegram ID
        save_user_credentials(user_id, username.strip(), password.strip())
        await update.message.reply_text("📡 Fetching your Overall attendance...")
        try:
            attendance = scrape_overall_attendance(creds["username"], creds["password"])
            await update.message.reply_text(attendance)
        except Exception as e:
            await update.message.reply_text(f"Invalid credentials! Please send correct: username,password")
    else:
        await update.message.reply_text("❌ You haven't sent your credentials yet!\nPlease send: username,password")


 
def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command)) 
    app.add_handler(CommandHandler("subjectwise", subjectwise_attendance))  
    app.add_handler(CommandHandler("overall", overall_attendance)) 
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
  
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_router))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), friendly_reply))
    print("✅ Bot is running")
    app.run_polling()
