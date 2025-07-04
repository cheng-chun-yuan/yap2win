import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ChatMemberHandler
from telegram.constants import ChatMemberStatus

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

# Load environment variables from .env file
load_dotenv()

# Dictionary to track which groups are being listened to
listening_groups = set()

# Dictionary to track user points by group
user_points = {}  # Format: {user_id: {group_id: points, group_name: name}}


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is a group admin"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if it's a group chat
    if chat.type not in ['group', 'supergroup']:
        return False
    
    try:
        # Get the user's status in the chat
        chat_member = await context.bot.get_chat_member(chat.id, user.id)
        # Check if user is admin or creator
        return chat_member.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to start listening to group chat"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if group ID is provided as argument
    if context.args:
        try:
            target_group_id = int(context.args[0])
            
            # Try to get information about the target group
            try:
                target_chat = await context.bot.get_chat(target_group_id)
                
                # Check if user is admin in the target group
                try:
                    chat_member = await context.bot.get_chat_member(target_group_id, user.id)
                    if chat_member.status not in ['administrator', 'creator']:
                        await update.message.reply_text(f"❌ You are not an admin in the group: {target_chat.title}")
                        return
                except Exception:
                    await update.message.reply_text("❌ Unable to verify your admin status in that group.")
                    return
                
                # Add group to listening groups
                listening_groups.add(target_group_id)
                
                # Log the action
                logger.info(f"Admin {user.first_name} (ID: {user.id}) started listening to group {target_chat.title} (ID: {target_group_id})")
                print(f"🔊 Admin {user.first_name} started listening to group {target_chat.title} (ID: {target_group_id})")
                
                # Send confirmation
                await update.message.reply_text(f"✅ Now listening to messages in **{target_chat.title}** (ID: {target_group_id})")
                
            except Exception as e:
                await update.message.reply_text(f"❌ Unable to access group with ID: {target_group_id}. Make sure the bot is added to that group.")
                logger.error(f"Error accessing group {target_group_id}: {e}")
                return
                
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Please provide a valid number.")
            return
    else:
        # No group ID provided, use current chat
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ Please provide a group ID or use this command in a group chat.\n\nUsage: `/start <group_id>`")
            return
        
        # Check if user is admin in current chat
        if not await is_admin(update, context):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Add current group to listening groups
        listening_groups.add(chat.id)
        
        # Log the action
        logger.info(f"Admin {user.first_name} (ID: {user.id}) started listening to group {chat.title} (ID: {chat.id})")
        print(f"🔊 Admin {user.first_name} started listening to group {chat.title} (ID: {chat.id})")
        
        # Send confirmation
        await update.message.reply_text(f"✅ Now listening to messages in **{chat.title}**")


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to stop listening to group chat"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if group ID is provided as argument
    if context.args:
        try:
            target_group_id = int(context.args[0])
            
            # Try to get information about the target group
            try:
                target_chat = await context.bot.get_chat(target_group_id)
                
                # Check if user is admin in the target group
                try:
                    chat_member = await context.bot.get_chat_member(target_group_id, user.id)
                    if chat_member.status not in ['administrator', 'creator']:
                        await update.message.reply_text(f"❌ You are not an admin in the group: {target_chat.title}")
                        return
                except Exception:
                    await update.message.reply_text("❌ Unable to verify your admin status in that group.")
                    return
                
                # Remove group from listening groups
                if target_group_id in listening_groups:
                    listening_groups.remove(target_group_id)
                    
                    # Log the action
                    logger.info(f"Admin {user.first_name} (ID: {user.id}) stopped listening to group {target_chat.title} (ID: {target_group_id})")
                    print(f"🔇 Admin {user.first_name} stopped listening to group {target_chat.title} (ID: {target_group_id})")
                    
                    # Send confirmation
                    await update.message.reply_text(f"✅ Stopped listening to messages in **{target_chat.title}** (ID: {target_group_id})")
                else:
                    await update.message.reply_text(f"❌ Not currently listening to **{target_chat.title}** (ID: {target_group_id})")
                
            except Exception as e:
                await update.message.reply_text(f"❌ Unable to access group with ID: {target_group_id}. Make sure the bot is added to that group.")
                logger.error(f"Error accessing group {target_group_id}: {e}")
                return
                
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Please provide a valid number.")
            return
    else:
        # No group ID provided, use current chat
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("❌ Please provide a group ID or use this command in a group chat.\n\nUsage: `/end <group_id>`")
            return
        
        # Check if user is admin in current chat
        if not await is_admin(update, context):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Remove current group from listening groups
        if chat.id in listening_groups:
            listening_groups.remove(chat.id)
            
            # Log the action
            logger.info(f"Admin {user.first_name} (ID: {user.id}) stopped listening to group {chat.title} (ID: {chat.id})")
            print(f"🔇 Admin {user.first_name} stopped listening to group {chat.title} (ID: {chat.id})")
            
            # Send confirmation
            await update.message.reply_text(f"✅ Stopped listening to messages in **{chat.title}**")
        else:
            await update.message.reply_text(f"❌ Not currently listening to **{chat.title}**")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show points status for user by group"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Only allow status command in private chat
    if chat.type != 'private':
        return
    
    # Check if group name is provided as argument
    if context.args:
        group_name = ' '.join(context.args)
        
        # Find groups that match the name (case insensitive)
        matching_groups = []
        for group_id, group_data in user_points.get(user.id, {}).items():
            if isinstance(group_data, dict) and group_data.get('group_name', '').lower() == group_name.lower():
                matching_groups.append((group_id, group_data))
        
        if matching_groups:
            status_text = f"📊 **Your Points in '{group_name}'**\n\n"
            for group_id, group_data in matching_groups:
                points = group_data.get('points', 0)
                status_text += f"• **{group_data.get('group_name', 'Unknown Group')}**: {points:.2f} points\n"
        else:
            status_text = f"❌ No points found for group '{group_name}'"
    else:
        # Show all groups
        user_group_points = user_points.get(user.id, {})
        
        if user_group_points:
            status_text = "📊 **Your Points by Group**\n\n"
            total_points = 0
            
            for group_id, group_data in user_group_points.items():
                if isinstance(group_data, dict):
                    points = group_data.get('points', 0)
                    group_name = group_data.get('group_name', 'Unknown Group')
                    status_text += f"• **{group_name}**: {points:.2f} points\n"
                    total_points += points
            
            status_text += f"\n🏆 **Total Points**: {total_points:.2f}"
        else:
            status_text = "❌ No points found. Start chatting in groups where the bot is listening!"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')
    
    # Log the status command
    logger.info(f"User {user.first_name} (ID: {user.id}) requested status")
    print(f"📊 User {user.first_name} (ID: {user.id}) requested status")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all available commands"""
    user = update.effective_user
    chat = update.effective_chat
    
    help_text = """
🤖 **Bot Commands**

📋 **General Commands:**
• `/help` - Show this help message
• `/hello` - Get a greeting from the bot
• `/status` - Show your points by group
• `/status <group_name>` - Show your points in specific group

👑 **Admin Commands (Group Admins Only):**
• `/start` - Start listening to messages in current group
• `/start <group_id>` - Start listening to messages in specific group
• `/end` - Stop listening to messages in current group
• `/end <group_id>` - Stop listening to messages in specific group

ℹ️ **How to use:**
1. Add me to your group(s)
2. Make sure I have admin permissions (recommended)
3. Group admins can use `/start` to activate message responses
4. Use `/start <group_id>` to activate listening for a specific group
5. The bot will only respond to messages in groups where listening is active
6. Use `/status` to check your points across all groups

💡 **Getting Group ID:**
• In your group, send any message and check the bot logs for the group ID
• Or use third-party bots like @userinfobot to get group information

📊 **Status:**
"""
    
    if chat.type in ['group', 'supergroup']:
        if chat.id in listening_groups:
            help_text += f"✅ Listening to messages in **{chat.title}**"
        else:
            help_text += f"❌ Not listening to messages in **{chat.title}**"
    else:
        help_text += "💬 This is a private chat"
    
    await update.message.reply_text(help_text, parse_mode='Markdown')
    
    # Log the help command
    logger.info(f"User {user.first_name} (ID: {user.id}) requested help")
    print(f"❓ User {user.first_name} (ID: {user.id}) requested help")


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Log user interaction
    user = update.effective_user
    logger.info(f"User {user.first_name} (ID: {user.id}) sent /hello command")
    print(f"👤 User {user.first_name} (ID: {user.id}) sent /hello command")
    
    # Send response
    response = f'hello {user.first_name}'
    await update.message.reply_text(response)
    
    # Log bot response
    logger.info(f"Bot responded to {user.first_name}: {response}")
    print(f"🤖 Bot responded to {user.first_name}: {response}")


# Add a general message handler to catch all text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print('=== MESSAGE RECEIVED ===')
    
    # Extract message details
    user = update.effective_user
    chat = update.effective_chat
    message = update.message
    
    # Log detailed message information
    message_info = {
        'userId': user.id if user else None,
        'chatId': chat.id if chat else None,
        'messageId': message.message_id if message else None,
        'text': message.text if message else None,
        'isCommand': message.text.startswith('/') if message and message.text else False,
        'chatType': chat.type if chat else None,
        'messageType': 'text' if message and message.text else 'other'
    }
    
    print('Message received:', message_info)
    
    # Skip bot commands - let command handlers process them
    if message and message.text and message.text.startswith('/'):
        print('Skipping command message - will be handled by command handlers')
        return
    
    # Only process text messages
    if not message or not message.text:
        print('Skipping non-text message')
        return
    
    # Extract required data
    userId = user.id if user else None
    chatId = chat.id if chat else None
    messageId = message.message_id if message else None
    text = message.text if message else None
    
    if not userId or not chatId or not messageId or not text:
        print('Missing required message data:', {
            'userId': userId, 
            'chatId': chatId, 
            'messageId': messageId, 
            'hasText': bool(text)
        })
        return
    
    # Log message processing
    text_preview = text[:50] + '...' if len(text) > 50 else text
    print(f'Processing message from user {userId} in chat {chatId}: "{text_preview}"')
    
    # Verification logic for private chat
    if chat.type == 'private' and text.lower().strip() == 'i am human':
        # TODO: Implement user verification service
        # await talkFiService.markUserAsVerified(userId)
        await message.reply_text('✅ You are now verified! You can join the group.')
        print(f'User {userId} verified in private chat')
        return
    
    # If in a group, check verification and kick if not verified
    if chat.type in ['group', 'supergroup'] and user:
        # TODO: Implement verification check
        # isVerified = await talkFiService.isUserVerified(userId)
        isVerified = True  # Temporary: assume all users are verified for now
        
        if not isVerified:
            try:
                await context.bot.send_message(
                    chat_id=userId,
                    text='You must verify with the bot in private chat by saying "I am human" before participating in the group.'
                )
            except Exception as e:
                print(f'Could not send DM to user {userId}: {e}')
            
            try:
                await context.bot.ban_chat_member(chat_id=chatId, user_id=userId)
                await context.bot.unban_chat_member(chat_id=chatId, user_id=userId)  # Unban immediately to kick
                print(f'Kicked unverified user {userId} from group {chatId}')
            except Exception as e:
                print(f'Could not kick user {userId} from group {chatId}: {e}')
            return
    
    # Only process messages from groups that are being listened to
    if chat.type in ['group', 'supergroup'] and chatId not in listening_groups:
        print(f'Skipping message from group {chatId} - not in listening groups')
        return
    
    try:
        # Get user info from Telegram context
        userInfo = {
            'username': user.username,
            'firstName': user.first_name,
            'lastName': user.last_name
        }
        
        # TODO: Implement message scoring service
        # score = await talkFiService.processMessage(
        #     messageId, userId, chatId, text, 
        #     int(time.time() * 1000),  # Current timestamp in milliseconds
        #     message.message_thread_id,
        #     message.reply_to_message.message_id if message.reply_to_message else None,
        #     [],  # Reactions will be handled separately if needed
        #     userInfo
        # )
        
        # Temporary scoring logic (replace with your actual scoring service)
        score = calculate_simple_score(text, userInfo)
        
        print(f'Message processed, score: {score}')
        print(f'User {userId} earned {score:.2f} points in chat {chatId}')
        
        # Track points by group
        if score > 0:
            if userId not in user_points:
                user_points[userId] = {}
            
            if chatId not in user_points[userId]:
                user_points[userId][chatId] = {
                    'points': 0,
                    'group_name': chat.title if chat.title else 'Unknown Group'
                }
            
            user_points[userId][chatId]['points'] += score
            user_points[userId][chatId]['group_name'] = chat.title if chat.title else 'Unknown Group'
            
            print(f"📊 Updated points for user {userId} in group {chat.title}: {user_points[userId][chatId]['points']:.2f}")
        
        # Log user message
        logger.info(f"User {user.first_name} (ID: {user.id}) sent message: {text}")
        print(f"💬 User {user.first_name} (ID: {user.id}) sent: {text}")
        
        # Send response based on score
        if score > 0:
            emoji = '🎉' if score >= 8 else '🎯' if score >= 5 else '✨'
            group_name = chat.title if chat.title else 'Unknown Group'
            response = f"{emoji} +{score:.2f} points from **{group_name}**! Keep engaging to earn more!"
            
            # Try to send to user's private chat instead of group
            try:
                await context.bot.send_message(
                    chat_id=userId,
                    text=response,
                    parse_mode='Markdown'
                )
                print(f"🎯 Sent {score:.2f} points notification to {user.first_name} in private chat (from {group_name})")
            except Exception as e:
                # If can't send to private chat, fall back to group reply
                print(f"Could not send DM to user {userId}: {e}")
                await message.reply_text(response, parse_mode='Markdown')
                print(f"🎯 User {user.first_name} earned {score:.2f} points! (sent in group)")
        else:
            # Do nothing for messages with 0 score
            print(f"🤖 No response for message with 0 score from {user.first_name}")
        
        # Log bot response only if there was one
        if score > 0:
            logger.info(f"Bot responded to {user.first_name}: {response}")
        
    except Exception as error:
        print(f'Error processing message: {error}')
        logger.error(f'Error processing message: {error}')
        # Don't reply with error to avoid spam, just log it


def calculate_simple_score(text: str, userInfo: dict) -> float:
    """Simple scoring function - replace with your actual scoring logic"""
    score = 0.0
    
    # Basic scoring based on message length and content
    if len(text) > 10:
        score += 1.0
    if len(text) > 50:
        score += 2.0
    
    # Bonus for questions
    if '?' in text:
        score += 1.5
    
    # Bonus for engagement words
    engagement_words = ['thanks', 'thank you', 'great', 'awesome', 'cool', 'nice', 'good']
    if any(word in text.lower() for word in engagement_words):
        score += 1.0
    
    # Bonus for emojis
    emoji_count = sum(1 for char in text if ord(char) > 127)
    score += min(emoji_count * 0.5, 3.0)
    
    return min(score, 10.0)  # Cap at 10 points


# Handler for when the bot is added to a group or its status changes
async def init_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_member = update.my_chat_member
    new_status = chat_member.new_chat_member.status
    old_status = chat_member.old_chat_member.status
    chat = chat_member.chat

    # Only act if the bot was added to a group or supergroup
    if new_status in ["member", "restricted"] and old_status == "left":
        logger.info(f"Bot added to group: {chat.title} (ID: {chat.id})")
        print(f"🤖 Bot added to group: {chat.title} (ID: {chat.id})")
        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "👋 Hi! Please add me as an admin to enable all features.\n"
                "Go to this group's settings > Administrators > Add Admin, then select me."
            )
        )

    # Optionally, notify if bot is removed or demoted
    elif new_status == "left" and old_status != "left":
        logger.info(f"Bot removed from group: {chat.title} (ID: {chat.id})")
        print(f"🤖 Bot removed from group: {chat.title} (ID: {chat.id})")


token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN environment variable is not set. Please create a .env file with your bot token.")

app = ApplicationBuilder().token(token).build()

app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("end", end))
app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("status", status))

# Add a message handler for all text messages (this should be added last)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Add a handler for my_chat_member events
app.add_handler(ChatMemberHandler(init_group, ChatMemberHandler.MY_CHAT_MEMBER))

print("🚀 Bot is starting...")
logger.info("Bot is starting...")

app.run_polling()