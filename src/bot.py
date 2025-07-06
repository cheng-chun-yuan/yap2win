import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ChatMemberHandler, ConversationHandler

from config.config import TOKEN, CHOOSING_GROUP, CHOOSING_TYPE, ENTERING_POOL_AMOUNT, ENTERING_RANK_AMOUNT, ENTERING_RANK_DISTRIBUTION, ENTERING_START_TIME, ENTERING_END_TIME, ENTERING_VERIFICATION_RULES, ENTERING_VERIFICATION_COUNTRY, ENTERING_VERIFICATION_AGE, ENTERING_VERIFICATION_NFT
from handlers.handlers import AdminHandlers, UserHandlers, BotHandlers, ROFLHandlers, VerificationHandlers
from handlers.reward_handlers import RewardHandlers
from handlers.message_handler import message_processor

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
app.add_handler(CommandHandler("help", UserHandlers.help_command))
app.add_handler(CommandHandler("init", AdminHandlers.start))
app.add_handler(CommandHandler("end", AdminHandlers.end))
app.add_handler(CommandHandler("hello", UserHandlers.hello))
app.add_handler(CommandHandler("status", UserHandlers.status))
app.add_handler(CommandHandler("leaderboard", UserHandlers.leaderboard))
app.add_handler(CommandHandler("reward", UserHandlers.reward))
app.add_handler(CommandHandler("rewards", UserHandlers.reward))  # Alias for /reward
app.add_handler(CommandHandler("result", UserHandlers.result))

# Add ROFL wallet commands
app.add_handler(CommandHandler("new_bot", ROFLHandlers.new_bot))
app.add_handler(CommandHandler("bot", ROFLHandlers.bot_info))
app.add_handler(CommandHandler("test", ROFLHandlers.test))

# Add verification commands  
app.add_handler(CommandHandler("verify", VerificationHandlers.verify_with_data))
# Keep old verification handlers for backwards compatibility
app.add_handler(CommandHandler("verify_old", VerificationHandlers.verify_user))
app.add_handler(CommandHandler("set_rule", VerificationHandlers.set_rule))

# Add conversation handler for set command
set_reward_handler = ConversationHandler(
    entry_points=[CommandHandler("set", RewardHandlers.set_reward)],
    states={
        CHOOSING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.choose_group)],
        CHOOSING_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.choose_type)],
        ENTERING_POOL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.enter_pool_amount)],
        ENTERING_RANK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.enter_rank_amount)],
        ENTERING_RANK_DISTRIBUTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.enter_rank_distribution)],
        ENTERING_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.enter_start_time)],
        ENTERING_END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.enter_end_time)],
        ENTERING_VERIFICATION_RULES: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.enter_verification_rules)],
        ENTERING_VERIFICATION_COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.enter_verification_country)],
        ENTERING_VERIFICATION_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.enter_verification_age)],
        ENTERING_VERIFICATION_NFT: [MessageHandler(filters.TEXT & ~filters.COMMAND, RewardHandlers.enter_verification_nft)],
    },
    fallbacks=[CommandHandler("cancel", RewardHandlers.cancel_reward_setup)],
)
app.add_handler(set_reward_handler)

# Add a message handler for all text messages (this should be added last)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_processor.handle_message))

# Add a handler for my_chat_member events
app.add_handler(ChatMemberHandler(BotHandlers.init_group, ChatMemberHandler.MY_CHAT_MEMBER))

print("🚀 Bot is starting...")
logger.info("Bot is starting...")

app.run_polling()