import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')
vision_model = genai.GenerativeModel('gemini-pro-vision')

# MongoDB setup
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['telegram_bot']
users_collection = db['users']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    users_collection.update_one(
        {'user_id': user.id},
        {'$set': {'username': user.username}},
        upsert=True
    )
    welcome_message = "👋 Hi! I'm your AI assistant powered by Google Gemini. I can help you with:\n" \
                     "- Text generation and conversations\n" \
                     "- Image analysis (just send me an image)\n" \
                     "Feel free to ask me anything!"
    await update.message.reply_text(welcome_message)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    try:
        response = model.generate_content(update.message.text)
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        await update.message.reply_text("Sorry, I encountered an error. Please try again.")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image messages."""
    try:
        # Get the image file
        photo = await update.message.photo[-1].get_file()
        
        # Generate response using vision model
        response = vision_model.generate_content([
            "Describe this image in detail",
            photo.file_path
        ])
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("Sorry, I couldn't process the image. Please try again.")

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
