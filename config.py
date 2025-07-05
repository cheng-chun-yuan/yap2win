"""
Configuration module for the Telegram bot.
Contains all constants and configuration values.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Bot token from environment
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable is not set. Please create a .env file with your bot token.")

# Conversation states for set_reward
CHOOSING_GROUP = 0
CHOOSING_TYPE = 1
ENTERING_POOL_AMOUNT = 2
ENTERING_RANK_AMOUNT = 3
ENTERING_RANK_DISTRIBUTION = 4
ENTERING_START_TIME = 5
ENTERING_END_TIME = 6

# Scoring configuration
MAX_SCORE = 10.0
ENGAGEMENT_WORDS = ['thanks', 'thank you', 'great', 'awesome', 'cool', 'nice', 'good']

# Scoring weights
SCORE_WEIGHTS = {
    'base_long_message': 1.0,
    'extra_long_message': 2.0,
    'question_bonus': 1.5,
    'engagement_bonus': 1.0,
    'emoji_multiplier': 0.5,
    'emoji_max_bonus': 3.0
}

# Message scoring thresholds
MESSAGE_LENGTH_THRESHOLD = 10
EXTRA_LENGTH_THRESHOLD = 50

# Bot response emojis
RESPONSE_EMOJIS = {
    'high_score': '🎉',
    'medium_score': '🎯',
    'low_score': '✨'
}

# Score thresholds for different emojis
EMOJI_THRESHOLDS = {
    'high': 8.0,
    'medium': 5.0
}

# Default rank distribution percentages
DEFAULT_RANK_DISTRIBUTION = {
    1: 0.5,  # 50% for 1st place
    2: 0.3,  # 30% for 2nd place
    3: 0.2   # 20% for 3rd place
}

# Verification message
VERIFICATION_MESSAGE = "i am human"
VERIFICATION_RESPONSE = "✅ You are now verified! You can join the group."

# Help text
HELP_TEXT = """
🤖 Bot Commands

📋 General Commands:
• `/help` - Show this help message
• `/hello` - Get a greeting from the bot
• `/status` - Show your points by group
• `/status <group_name>` - Show your points in specific group

👑 Admin Commands (Group Admins Only):
• `/start` - Start listening to messages in current group
• `/start <group_id>` - Start listening to messages in specific group
• `/end` - Stop listening to messages in current group
• `/end <group_id>` - Stop listening to messages in specific group
• `/set_reward` - Set reward configuration (private chat only)

ℹ️ How to use:
1. Add me to your group(s)
2. Make sure I have admin permissions (recommended)
3. Group admins can use `/start` to activate message responses
4. Use `/start <group_id>` to activate listening for a specific group
5. The bot will only respond to messages in groups where listening is active
6. Use `/status` to check your points across all groups
7. Use `/set_reward` in private chat to configure rewards

💡 Getting Group ID:
• In your group, send any message and check the bot logs for the group ID
• Or use third-party bots like @userinfobot to get group information

📊 Status:
"""

# Admin permissions required
ADMIN_STATUSES = ['administrator', 'creator']

# Chat types
GROUP_CHAT_TYPES = ['group', 'supergroup']
PRIVATE_CHAT_TYPE = 'private'

# Event statuses
EVENT_STATUS_ACTIVE = 'active'
EVENT_STATUS_FINISHED = 'finished'

# Reward types
REWARD_TYPE_POOL = 'pool'
REWARD_TYPE_RANK = 'rank'

# Bot status messages
BOT_INIT_MESSAGE = (
    "👋 Hi! Please add me as an admin to enable all features.\n"
    "Go to this group's settings > Administrators > Add Admin, then select me."
)

# Date format for event times
DATE_FORMAT = '%Y-%m-%d %H:%M'