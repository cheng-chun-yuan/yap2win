import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ChatMemberHandler, ConversationHandler

from config import TOKEN, CHOOSING_GROUP, CHOOSING_TYPE, ENTERING_POOL_AMOUNT, ENTERING_RANK_AMOUNT, ENTERING_RANK_DISTRIBUTION, ENTERING_START_TIME, ENTERING_END_TIME
from handlers import admin_handlers, user_handlers, bot_handlers
from reward_handlers import reward_handlers
from message_handler import message_processor

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Reduce verbose logging from httpx and other libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.INFO)


# Build the application
app = ApplicationBuilder().token(TOKEN).build()

# Add command handlers
app.add_handler(CommandHandler("help", user_handlers.help_command))
app.add_handler(CommandHandler("init", admin_handlers.start))
app.add_handler(CommandHandler("end", admin_handlers.end))
app.add_handler(CommandHandler("hello", user_handlers.hello))
app.add_handler(CommandHandler("status", user_handlers.status))
app.add_handler(CommandHandler("leaderboard", user_handlers.leaderboard))
app.add_handler(CommandHandler("reward", user_handlers.reward))
app.add_handler(CommandHandler("rewards", user_handlers.reward))  # Alias for /reward
app.add_handler(CommandHandler("result", user_handlers.result))

# Add conversation handler for set command
set_reward_handler = ConversationHandler(
    entry_points=[CommandHandler("set", reward_handlers.set_reward)],
    states={
        CHOOSING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, reward_handlers.choose_group)],
        CHOOSING_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reward_handlers.choose_type)],
        ENTERING_POOL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reward_handlers.enter_pool_amount)],
        ENTERING_RANK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reward_handlers.enter_rank_amount)],
        ENTERING_RANK_DISTRIBUTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reward_handlers.enter_rank_distribution)],
        ENTERING_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reward_handlers.enter_start_time)],
        ENTERING_END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reward_handlers.enter_end_time)],
    },
    fallbacks=[CommandHandler("cancel", reward_handlers.cancel_reward_setup)],
)
app.add_handler(set_reward_handler)

# Add a message handler for all text messages (this should be added last)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_processor.handle_message))

# Add a handler for my_chat_member events
app.add_handler(ChatMemberHandler(bot_handlers.init_group, ChatMemberHandler.MY_CHAT_MEMBER))

print("🚀 Bot is starting...")
logger.info("Bot is starting...")

app.run_polling()