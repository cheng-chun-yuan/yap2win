import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ChatMemberHandler, ConversationHandler
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

# Dictionary to track reward configurations (one per group)
reward_configs = {}  # Format: {group_id: {'type': 'pool'|'rank', 'total_amount': float, 'rank_rewards': {rank: amount}, 'start_time': timestamp, 'end_time': timestamp, 'status': 'active'|'finished'}}

# Dictionary to track event participants
event_participants = {}  # Format: {group_id: {user_id: {'points': float, 'username': str, 'first_name': str}}}

# Conversation states for set_reward
CHOOSING_GROUP, CHOOSING_TYPE, ENTERING_POOL_AMOUNT, ENTERING_RANK_AMOUNT, ENTERING_RANK_DISTRIBUTION, ENTERING_START_TIME, ENTERING_END_TIME = range(7)


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
                await update.message.reply_text(f"✅ Now listening to messages in {target_chat.title} (ID: {target_group_id})")
                
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
        await update.message.reply_text(f"✅ Now listening to messages in {chat.title}")


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
                    await update.message.reply_text(f"✅ Stopped listening to messages in {target_chat.title} (ID: {target_group_id})")
                else:
                    await update.message.reply_text(f"❌ Not currently listening to {target_chat.title} (ID: {target_group_id})")
                
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
            await update.message.reply_text(f"✅ Stopped listening to messages in {chat.title}")
        else:
            await update.message.reply_text(f"❌ Not currently listening to {chat.title}")


async def set_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to set reward configuration - only works in private chat"""
    user = update.effective_user
    chat = update.effective_chat
    
    # Only allow in private chat
    if chat.type != 'private':
        return
    
    # Check if user is admin in any group where bot is listening
    admin_groups = []
    for group_id in listening_groups:
        try:
            chat_member = await context.bot.get_chat_member(group_id, user.id)
            if chat_member.status in ['administrator', 'creator']:
                group_info = await context.bot.get_chat(group_id)
                admin_groups.append((group_id, group_info.title))
        except Exception:
            continue
    
    if not admin_groups:
        await update.message.reply_text("❌ You need to be an admin in at least one group where the bot is listening to set rewards.")
        return ConversationHandler.END
    
    # Show available groups
    groups_text = "🏆 Set Reward Configuration\n\n"
    groups_text += "Available groups where you are admin:\n\n"
    
    for i, (group_id, group_name) in enumerate(admin_groups, 1):
        current_config = reward_configs.get(group_id, {})
        config_type = current_config.get('type', 'None')
        total_amount = current_config.get('total_amount', 0)
        
        groups_text += f"{i}. {group_name} (ID: {group_id})\n"
        if config_type != 'None':
            groups_text += f"   └ Current: {config_type.title()} reward - {total_amount}\n"
        else:
            groups_text += f"   └ No reward set\n"
    
    groups_text += "\nReply with the number of the group you want to configure:"
    
    # Store admin groups in context for later use
    context.user_data['admin_groups'] = admin_groups
    
    await update.message.reply_text(groups_text, parse_mode='Markdown')
    return CHOOSING_GROUP


async def choose_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle group selection"""
    user = update.effective_user
    text = update.message.text.strip()
    
    try:
        group_index = int(text) - 1
        admin_groups = context.user_data.get('admin_groups', [])
        
        if 0 <= group_index < len(admin_groups):
            selected_group_id, selected_group_name = admin_groups[group_index]
            context.user_data['selected_group_id'] = selected_group_id
            context.user_data['selected_group_name'] = selected_group_name
            
            # Check if group already has a reward
            current_config = reward_configs.get(selected_group_id, {})
            if current_config:
                config_type = current_config.get('type', '')
                total_amount = current_config.get('total_amount', 0)
                
                await update.message.reply_text(
                    f"⚠️ {selected_group_name} already has a {config_type} reward of {total_amount}.\n\n"
                    f"Setting a new reward will replace the current one.\n\n"
                    f"Choose reward type:\n"
                    f"• Reply `pool` for equal distribution\n"
                    f"• Reply `rank` for rank-based distribution"
                )
            else:
                await update.message.reply_text(
                    f"✅ Selected: {selected_group_name}\n\n"
                    f"Choose reward type:\n"
                    f"• Reply `pool` for equal distribution\n"
                    f"• Reply `rank` for rank-based distribution"
                )
            
            return CHOOSING_TYPE
        else:
            await update.message.reply_text("❌ Invalid group number. Please try again.")
            return CHOOSING_GROUP
    except ValueError:
        await update.message.reply_text("❌ Please reply with a number.")
        return CHOOSING_GROUP


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle reward type selection"""
    text = update.message.text.strip().lower()
    selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
    
    if text == 'pool':
        context.user_data['reward_type'] = 'pool'
        await update.message.reply_text(
            f"🏆 Pool Reward for {selected_group_name}\n\n"
            f"Enter the total reward amount (e.g., 1000):"
        )
        return ENTERING_POOL_AMOUNT
    
    elif text == 'rank':
        context.user_data['reward_type'] = 'rank'
        await update.message.reply_text(
            f"🏆 Rank Reward for {selected_group_name}\n\n"
            f"Enter the total reward amount (e.g., 1000):"
        )
        return ENTERING_RANK_AMOUNT
    
    else:
        await update.message.reply_text("❌ Please reply with `pool` or `rank`.")
        return CHOOSING_TYPE


async def enter_pool_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pool reward amount input"""
    text = update.message.text.strip()
    selected_group_id = context.user_data.get('selected_group_id')
    selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
    
    try:
        total_amount = float(text)
        if total_amount <= 0:
            await update.message.reply_text("❌ Amount must be positive. Please try again:")
            return ENTERING_POOL_AMOUNT
        
        # Store the reward configuration temporarily
        context.user_data['reward_config'] = {
            'type': 'pool',
            'total_amount': total_amount,
            'group_name': selected_group_name
        }
        
        await update.message.reply_text(
            f"🏆 Pool Reward for {selected_group_name}\n\n"
            f"Total Amount: {total_amount}\n\n"
            f"Enter the start time (YYYY-MM-DD HH:MM):\n"
            f"Example: 2024-01-15 14:30"
        )
        
        return ENTERING_START_TIME
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number:")
        return ENTERING_POOL_AMOUNT


async def enter_rank_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle rank reward amount input"""
    text = update.message.text.strip()
    selected_group_id = context.user_data.get('selected_group_id')
    selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
    
    try:
        total_amount = float(text)
        if total_amount <= 0:
            await update.message.reply_text("❌ Amount must be positive. Please try again:")
            return ENTERING_RANK_AMOUNT
        
        context.user_data['total_amount'] = total_amount
        
        await update.message.reply_text(
            f"🏆 Rank Reward for {selected_group_name}\n\n"
            f"Total Amount: {total_amount}\n\n"
            f"Choose distribution:\n"
            f"• Reply `default` for 50% (1st), 30% (2nd), 20% (3rd)\n"
            f"• Reply `custom` to set your own amounts\n"
            f"• Reply `custom 600 300 100` to set specific amounts"
        )
        return ENTERING_RANK_DISTRIBUTION
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number:")
        return ENTERING_RANK_AMOUNT


async def enter_rank_distribution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle rank distribution input"""
    text = update.message.text.strip().lower()
    selected_group_id = context.user_data.get('selected_group_id')
    selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
    total_amount = context.user_data.get('total_amount', 0)
    
    if text == 'default':
        # Default rank distribution (top 3)
        default_ranks = {
            1: total_amount * 0.5,  # 50% for 1st place
            2: total_amount * 0.3,  # 30% for 2nd place
            3: total_amount * 0.2   # 20% for 3rd place
        }
        
        # Store the reward configuration temporarily
        context.user_data['reward_config'] = {
            'type': 'rank',
            'total_amount': total_amount,
            'rank_rewards': default_ranks,
            'group_name': selected_group_name
        }
        
        rank_text = "\n".join([f"• Rank {rank}: {amount:.2f}" for rank, amount in default_ranks.items()])
        
        await update.message.reply_text(
            f"🏆 Rank Reward for {selected_group_name}\n\n"
            f"Total Amount: {total_amount}\n"
            f"Default Distribution:\n{rank_text}\n\n"
            f"Enter the start time (YYYY-MM-DD HH:MM):\n"
            f"Example: 2024-01-15 14:30"
        )
        
        return ENTERING_START_TIME
    
    elif text.startswith('custom'):
        # Parse custom amounts
        parts = text.split()
        if len(parts) > 1:
            try:
                custom_amounts = [float(amount) for amount in parts[1:]]
                rank_rewards = {i+1: amount for i, amount in enumerate(custom_amounts)}
                
                # Validate that rank amounts sum to total
                if abs(sum(custom_amounts) - total_amount) > 0.01:  # Allow small floating point differences
                    await update.message.reply_text(
                        f"❌ Rank amounts ({sum(custom_amounts)}) must equal total amount ({total_amount}).\n"
                        f"Please try again:"
                    )
                    return ENTERING_RANK_DISTRIBUTION
                
                # Store the reward configuration temporarily
                context.user_data['reward_config'] = {
                    'type': 'rank',
                    'total_amount': total_amount,
                    'rank_rewards': rank_rewards,
                    'group_name': selected_group_name
                }
                
                rank_text = "\n".join([f"• Rank {rank}: {amount}" for rank, amount in rank_rewards.items()])
                
                await update.message.reply_text(
                    f"🏆 Rank Reward for {selected_group_name}\n\n"
                    f"Total Amount: {total_amount}\n"
                    f"Custom Distribution:\n{rank_text}\n\n"
                    f"Enter the start time (YYYY-MM-DD HH:MM):\n"
                    f"Example: 2024-01-15 14:30"
                )
                
                return ENTERING_START_TIME
            except ValueError:
                await update.message.reply_text("❌ Invalid amounts. Please use format: `custom 600 300 100`")
                return ENTERING_RANK_DISTRIBUTION
        else:
            await update.message.reply_text(
                "❌ Please specify custom amounts.\n"
                f"Example: `custom 600 300 100` for 3 ranks\n"
                f"Or reply `default` for default distribution"
            )
            return ENTERING_RANK_DISTRIBUTION
    
    else:
        await update.message.reply_text(
            "❌ Please reply with:\n"
            f"• `default` for default distribution\n"
            f"• `custom 600 300 100` for custom amounts"
        )
        return ENTERING_RANK_DISTRIBUTION


async def enter_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle start time input"""
    text = update.message.text.strip()
    selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
    
    try:
        # Parse datetime (YYYY-MM-DD HH:MM format)
        from datetime import datetime
        start_time = datetime.strptime(text, '%Y-%m-%d %H:%M')
        
        # Store start time
        context.user_data['start_time'] = start_time
        
        await update.message.reply_text(
            f"🏆 Event Start Time Set\n\n"
            f"Group: {selected_group_name}\n"
            f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Enter the end time (YYYY-MM-DD HH:MM):\n"
            f"Example: 2024-01-15 18:30"
        )
        
        return ENTERING_END_TIME
        
    except ValueError:
        await update.message.reply_text("❌ Invalid date format. Please use YYYY-MM-DD HH:MM format:\nExample: 2024-01-15 14:30")
        return ENTERING_START_TIME


async def enter_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle end time input and complete reward setup"""
    text = update.message.text.strip()
    selected_group_id = context.user_data.get('selected_group_id')
    selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
    start_time = context.user_data.get('start_time')
    reward_config = context.user_data.get('reward_config', {})
    
    try:
        # Parse datetime (YYYY-MM-DD HH:MM format)
        from datetime import datetime
        end_time = datetime.strptime(text, '%Y-%m-%d %H:%M')
        
        # Validate end time is after start time
        if end_time <= start_time:
            await update.message.reply_text("❌ End time must be after start time. Please try again:")
            return ENTERING_END_TIME
        
        # Complete the reward configuration
        reward_configs[selected_group_id] = {
            **reward_config,
            'start_time': start_time,
            'end_time': end_time,
            'status': 'active'
        }
        
        # Initialize event participants
        event_participants[selected_group_id] = {}
        
        # Format the confirmation message
        if reward_config['type'] == 'pool':
            confirmation = (
                f"✅ Pool Reward Event Set Successfully!\n\n"
                f"Group: {selected_group_name}\n"
                f"Type: Pool\n"
                f"Total Amount: {reward_config['total_amount']}\n"
                f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"End Time: {end_time.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Rewards will be distributed equally among all participants."
            )
        else:  # rank type
            rank_rewards = reward_config.get('rank_rewards', {})
            rank_text = "\n".join([f"• Rank {rank}: {amount:.2f}" for rank, amount in rank_rewards.items()])
            confirmation = (
                f"✅ Rank Reward Event Set Successfully!\n\n"
                f"Group: {selected_group_name}\n"
                f"Type: Rank\n"
                f"Total Amount: {reward_config['total_amount']}\n"
                f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"End Time: {end_time.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Rank Distribution:\n{rank_text}"
            )
        
        await update.message.reply_text(confirmation)
        
        # Send event announcement to the group
        try:
            if reward_config['type'] == 'pool':
                group_announcement = (
                    f"🎉 NEW POOL EVENT STARTING!\n\n"
                    f"Total Reward: {reward_config['total_amount']}\n"
                    f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"End Time: {end_time.strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"Start chatting to earn points! Everyone who participates will get an equal share of the reward pool."
                )
            else:  # rank type
                rank_rewards = reward_config.get('rank_rewards', {})
                rank_text = "\n".join([f"• Rank {rank}: {amount:.2f}" for rank, amount in rank_rewards.items()])
                group_announcement = (
                    f"🏆 NEW RANK EVENT STARTING!\n\n"
                    f"Total Reward: {reward_config['total_amount']}\n"
                    f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"End Time: {end_time.strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"Rank Distribution:\n{rank_text}\n\n"
                    f"Start chatting to earn points and climb the rankings!"
                )
            
            # Send announcement to group
            sent_announcement = await context.bot.send_message(
                chat_id=selected_group_id,
                text=group_announcement
            )
            
            # Try to pin the announcement
            try:
                await context.bot.pin_chat_message(
                    chat_id=selected_group_id,
                    message_id=sent_announcement.message_id,
                    disable_notification=False
                )
                print(f"📌 Event announcement pinned in {selected_group_name} (ID: {selected_group_id})")
            except Exception as e:
                print(f"Could not pin announcement in group {selected_group_id}: {e}")
            
            print(f"📢 Event announcement sent to {selected_group_name} (ID: {selected_group_id})")
            
        except Exception as e:
            print(f"Could not send event announcement to group {selected_group_id}: {e}")
        
        # Log the action
        logger.info(f"Admin set {reward_config['type']} reward event for group {selected_group_name} (ID: {selected_group_id}): {reward_config['total_amount']} from {start_time} to {end_time}")
        print(f"🏆 {reward_config['type'].title()} reward event set for group {selected_group_name}: {reward_config['total_amount']} ({start_time} - {end_time})")
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Invalid date format. Please use YYYY-MM-DD HH:MM format:\nExample: 2024-01-15 18:30")
        return ENTERING_END_TIME


async def cancel_reward_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the reward setup process"""
    await update.message.reply_text("❌ Reward setup cancelled.")
    return ConversationHandler.END


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
            status_text = f"📊 Your Points in '{group_name}'\n\n"
            for group_id, group_data in matching_groups:
                points = group_data.get('points', 0)
                status_text += f"• {group_data.get('group_name', 'Unknown Group')}: {points:.2f} points\n"
        else:
            status_text = f"❌ No points found for group '{group_name}'"
    else:
        # Show all groups
        user_group_points = user_points.get(user.id, {})
        
        if user_group_points:
            status_text = "📊 Your Points by Group\n\n"
            total_points = 0
            
            for group_id, group_data in user_group_points.items():
                if isinstance(group_data, dict):
                    points = group_data.get('points', 0)
                    group_name = group_data.get('group_name', 'Unknown Group')
                    status_text += f"• {group_name}: {points:.2f} points\n"
                    total_points += points
            
            status_text += f"\n🏆 Total Points: {total_points:.2f}"
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
    
    if chat.type in ['group', 'supergroup']:
        if chat.id in listening_groups:
            help_text += f"✅ Listening to messages in {chat.title}"
        else:
            help_text += f"❌ Not listening to messages in {chat.title}"
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
            
            # Track participants for active events
            if chatId in reward_configs and reward_configs[chatId].get('status') == 'active':
                if chatId not in event_participants:
                    event_participants[chatId] = {}
                
                if userId not in event_participants[chatId]:
                    event_participants[chatId][userId] = {
                        'points': 0,
                        'username': user.username,
                        'first_name': user.first_name
                    }
                
                event_participants[chatId][userId]['points'] += score
                event_participants[chatId][userId]['username'] = user.username
                event_participants[chatId][userId]['first_name'] = user.first_name
                
                print(f"🎯 Event participant {user.first_name} earned {score:.2f} points in {chat.title}")
        
        # Log user message
        logger.info(f"User {user.first_name} (ID: {user.id}) sent message: {text}")
        print(f"💬 User {user.first_name} (ID: {user.id}) sent: {text}")
        
        # Send response based on score
        if score > 0:
            emoji = '🎉' if score >= 8 else '🎯' if score >= 5 else '✨'
            group_name = chat.title if chat.title else 'Unknown Group'
            response = f"{emoji} +{score:.2f} points from {group_name}! Keep engaging to earn more!"
            
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
        
        # Check if any events have finished
        await check_finished_events(context)
        
    except Exception as error:
        print(f'Error processing message: {error}')
        logger.error(f'Error processing message: {error}')
        # Don't reply with error to avoid spam, just log it


async def check_finished_events(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check for finished events and send results to groups"""
    from datetime import datetime
    current_time = datetime.now()
    
    for group_id, config in reward_configs.items():
        if config.get('status') == 'active' and config.get('end_time'):
            if current_time >= config['end_time']:
                # Event has finished
                await send_event_results(context, group_id, config)


async def send_event_results(context: ContextTypes.DEFAULT_TYPE, group_id: int, config: dict) -> None:
    """Send event results to the group"""
    try:
        group_name = config.get('group_name', 'Unknown Group')
        event_type = config.get('type', 'unknown')
        total_amount = config.get('total_amount', 0)
        
        # Mark event as finished
        reward_configs[group_id]['status'] = 'finished'
        
        # Get participants for this event
        participants = event_participants.get(group_id, {})
        
        if not participants:
            # No participants
            result_message = (
                f"🏆 Event Finished - No Participants\n\n"
                f"Event: {group_name}\n"
                f"Type: {event_type.title()}\n"
                f"Total Reward: {total_amount}\n"
                f"Status: No participants joined the event"
            )
        else:
            # Sort participants by points
            sorted_participants = sorted(
                participants.items(), 
                key=lambda x: x[1]['points'], 
                reverse=True
            )
            
            if event_type == 'pool':
                # Pool distribution - equal share for all participants
                participant_count = len(sorted_participants)
                if participant_count > 0:
                    share_per_person = total_amount / participant_count
                    
                    result_message = f"🏆 Pool Event Results - {group_name}\n\n"
                    result_message += f"Total Reward: {total_amount}\n"
                    result_message += f"Participants: {participant_count}\n"
                    result_message += f"Share per person: {share_per_person:.2f}\n\n"
                    result_message += "Final Rankings:\n"
                    
                    for i, (user_id, user_data) in enumerate(sorted_participants, 1):
                        username = user_data.get('username', 'Unknown')
                        first_name = user_data.get('first_name', 'Unknown')
                        points = user_data.get('points', 0)
                        display_name = f"@{username}" if username else first_name
                        result_message += f"{i}. {display_name}: {points:.2f} points\n"
                
            else:  # rank type
                # Rank distribution
                rank_rewards = config.get('rank_rewards', {})
                
                result_message = f"🏆 Rank Event Results - {group_name}\n\n"
                result_message += f"Total Reward: {total_amount}\n"
                result_message += f"Participants: {len(sorted_participants)}\n\n"
                result_message += "Final Rankings:\n"
                
                for i, (user_id, user_data) in enumerate(sorted_participants, 1):
                    username = user_data.get('username', 'Unknown')
                    first_name = user_data.get('first_name', 'Unknown')
                    points = user_data.get('points', 0)
                    display_name = f"@{username}" if username else first_name
                    
                    # Get reward for this rank
                    reward = rank_rewards.get(i, 0)
                    reward_text = f" (+{reward:.2f})" if reward > 0 else ""
                    
                    result_message += f"{i}. {display_name}: {points:.2f} points{reward_text}\n"
        
        # Send results to the group
        sent_message = await context.bot.send_message(
            chat_id=group_id,
            text=result_message
        )
        
        # Try to pin the results message
        try:
            await context.bot.pin_chat_message(
                chat_id=group_id,
                message_id=sent_message.message_id,
                disable_notification=False
            )
            print(f"📌 Event results pinned in {group_name} (ID: {group_id})")
        except Exception as e:
            print(f"Could not pin message in group {group_id}: {e}")
        
        print(f"🏆 Event results sent to {group_name} (ID: {group_id})")
        logger.info(f"Event results sent to group {group_name} (ID: {group_id})")
        
    except Exception as e:
        print(f"Error sending event results to group {group_id}: {e}")
        logger.error(f"Error sending event results to group {group_id}: {e}")


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

# Add conversation handler for set_reward
set_reward_handler = ConversationHandler(
    entry_points=[CommandHandler("set_reward", set_reward)],
    states={
        CHOOSING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_group)],
        CHOOSING_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_type)],
        ENTERING_POOL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_pool_amount)],
        ENTERING_RANK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_rank_amount)],
        ENTERING_RANK_DISTRIBUTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_rank_distribution)],
        ENTERING_START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_start_time)],
        ENTERING_END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_end_time)],
    },
    fallbacks=[CommandHandler("cancel", cancel_reward_setup)],
)
app.add_handler(set_reward_handler)

# Add a message handler for all text messages (this should be added last)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Add a handler for my_chat_member events
app.add_handler(ChatMemberHandler(init_group, ChatMemberHandler.MY_CHAT_MEMBER))

print("🚀 Bot is starting...")
logger.info("Bot is starting...")

app.run_polling()