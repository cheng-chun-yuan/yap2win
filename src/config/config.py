"""
Configuration module for the Telegram bot.
Contains all constants and configuration values.
"""
import os

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN environment variable is not set. Please create a .env file with your bot token.")

DEFAULT_POOL_AMOUNT = 1  # Default 1.0 ROSE

# Conversation states for set_reward
CHOOSING_GROUP = 0
CHOOSING_TYPE = 1
ENTERING_POOL_AMOUNT = 2
ENTERING_RANK_AMOUNT = 3
ENTERING_RANK_DISTRIBUTION = 4
ENTERING_START_TIME = 5
ENTERING_END_TIME = 6
ENTERING_VERIFICATION_RULES = 7
ENTERING_VERIFICATION_COUNTRY = 8
ENTERING_VERIFICATION_AGE = 9
ENTERING_VERIFICATION_NFT = 10

# DeepEval LLM-as-a-Judge Scoring Configuration
MAX_SCORE = 10.0

# DeepEval scoring criteria and weights
DEEPEVAL_CONFIG = {
    'model': 'gpt-4',
    'max_score': 10.0,
    'fallback_score': 5.0,
    'engagement_criteria': [
        'Encourages discussion and interaction',
        'Shows genuine interest in others\' opinions',
        'Uses inclusive and welcoming language',
        'Asks thoughtful questions',
        'Provides helpful or informative content',
        'Uses appropriate emojis and tone',
        'Avoids spam, trolling, or negative behavior',
        'Contributes meaningfully to the conversation'
    ]
}

# Bot response emojis for DeepEval scores
RESPONSE_EMOJIS = {
    'high_score': '🎉',    # 8-10 points
    'medium_score': '🎯',  # 6-7 points
    'low_score': '✨',     # 4-5 points
    'basic_score': '💬'    # 0-3 points
}

# Score thresholds for different emojis
EMOJI_THRESHOLDS = {
    'high': 8.0,
    'medium': 6.0,
    'low': 4.0
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
• `/leaderboard` - Show current event rankings (group only)
• `/reward` or `/rewards` - Show current event information (group only)
• `/result` - Show current standings or final results (group only)

👑 Admin Commands (Group Admins Only):
• `/init` - Start listening to messages in current group
• `/init <group_id>` - Start listening to messages in specific group
• `/end` - Stop listening to messages in current group
• `/end <group_id>` - Stop listening to messages in specific group
• `/set` - Set reward configuration (private chat only)

🏆 Event Commands:
• `/leaderboard` - View current rankings and points
• `/reward` or `/rewards` - View event details, rewards, and time remaining
• `/result` - View current standings (during event) or final results (after event)

🤖 AI-Powered Scoring:
• Messages are automatically scored (0-10 points) using AI
• Scoring considers: engagement, helpfulness, inclusivity, and conversation quality
• Points are awarded for meaningful contributions and positive interactions
• Spam, trolling, or irrelevant content receives low scores

ℹ️ How to use:
1. Add me to your group(s)
2. Make sure I have admin permissions (recommended)
3. Group admins can use `/init` to activate message responses
4. Use `/init <group_id>` to activate listening for a specific group
5. The bot will always track points and send notifications in all groups
6. Event participation only happens in groups where listening is active
7. Use `/status` to check your points across all groups
8. Use `/set` in private chat to configure rewards
9. Use `/leaderboard`, `/reward`, or `/result` to check event progress

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

# Smart Contract Configuration
CONTRACT_ADDRESS = "0xf3Fa41af708b8c5329410A2b2bF4cA04a5F832B2"
CONTRACT_NETWORK = "Oasis Sapphire"
CONTRACT_RPC_URL = "https://sapphire.oasis.io"

# ROFL Configuration
ROFL_SOCKET_PATH = "/run/rofl-appd.sock"
ROFL_BASE_URL = "http://localhost"