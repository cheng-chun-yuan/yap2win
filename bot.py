import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Log user interaction
    user = update.effective_user
    logger.info(f"User {user.first_name} (ID: {user.id}) sent /hello command")
    print(f"👤 User {user.first_name} (ID: {user.id}) sent /hello command")
    
    # Send response
    response = f'Hello {user.first_name}'
    await update.message.reply_text(response)
    
    # Log bot response
    logger.info(f"Bot responded to {user.first_name}: {response}")
    print(f"🤖 Bot responded to {user.first_name}: {response}")


# Add a general message handler to catch all text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Log user message
    user = update.effective_user
    message_text = update.message.text
    logger.info(f"User {user.first_name} (ID: {user.id}) sent message: {message_text}")
    print(f"💬 User {user.first_name} (ID: {user.id}) sent: {message_text}")
    
    # Send a default response for unrecognized messages
    response = "I received your message! Use /hello to get a greeting."
    await update.message.reply_text(response)
    
    # Log bot response
    logger.info(f"Bot responded to {user.first_name}: {response}")
    print(f"🤖 Bot responded to {user.first_name}: {response}")


token = os.getenv("BOT_TOKEN")
if not token:
    raise ValueError("BOT_TOKEN environment variable is not set. Please create a .env file with your bot token.")

app = ApplicationBuilder().token(token).build()

app.add_handler(CommandHandler("hello", hello))

# Add a message handler for all text messages (this should be added last)
from telegram.ext import MessageHandler, filters
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚀 Bot is starting...")
logger.info("Bot is starting...")

app.run_polling()