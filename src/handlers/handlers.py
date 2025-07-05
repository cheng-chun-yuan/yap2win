"""
Command handlers module for the Telegram bot.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config.config import (
    CHOOSING_GROUP, CHOOSING_TYPE, ENTERING_POOL_AMOUNT, ENTERING_RANK_AMOUNT,
    ENTERING_RANK_DISTRIBUTION, ENTERING_START_TIME, ENTERING_END_TIME,
    ADMIN_STATUSES, GROUP_CHAT_TYPES, PRIVATE_CHAT_TYPE, HELP_TEXT, DATE_FORMAT,
    REWARD_TYPE_POOL, REWARD_TYPE_RANK, BOT_INIT_MESSAGE
)
from services.data_storage import data_storage
from services.reward_system import reward_system
from services.rofl_service import rofl_service

logger = logging.getLogger(__name__)


class AdminHandlers:
    """Handles admin-related commands."""
    
    @staticmethod
    async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if the user is a group admin."""
        user = update.effective_user
        chat = update.effective_chat
        
        if chat.type not in GROUP_CHAT_TYPES:
            return False
        
        try:
            chat_member = await context.bot.get_chat_member(chat.id, user.id)
            return chat_member.status in ADMIN_STATUSES
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin command to start listening to group chat."""
        user = update.effective_user
        chat = update.effective_chat
        
        if context.args:
            await AdminHandlers._handle_start_with_group_id(update, context, user, context.args[0])
        else:
            await AdminHandlers._handle_start_current_group(update, context, user, chat)
    
    @staticmethod
    async def _handle_start_with_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                        user: Any, group_id_str: str) -> None:
        """Handle start command with group ID argument."""
        try:
            target_group_id = int(group_id_str)
            target_chat = await context.bot.get_chat(target_group_id)
            
            # Check if user is admin in the target group
            try:
                chat_member = await context.bot.get_chat_member(target_group_id, user.id)
                if chat_member.status not in ADMIN_STATUSES:
                    await update.message.reply_text(f"❌ You are not an admin in the group: {target_chat.title}")
                    return
            except Exception:
                await update.message.reply_text("❌ Unable to verify your admin status in that group.")
                return
            
            # Add group to listening groups
            data_storage.add_listening_group(target_group_id)
            
            # Log the action
            logger.info(f"Admin {user.first_name} (ID: {user.id}) started listening to group {target_chat.title} (ID: {target_group_id})")
            print(f"🔊 Admin {user.first_name} started listening to group {target_chat.title} (ID: {target_group_id})")
            
            # Send confirmation
            await update.message.reply_text(f"✅ Now listening to messages in {target_chat.title} (ID: {target_group_id})")
            
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Please provide a valid number.")
        except Exception as e:
            await update.message.reply_text(f"❌ Unable to access group with ID: {group_id_str}. Make sure the bot is added to that group.")
            logger.error(f"Error accessing group {group_id_str}: {e}")
    
    @staticmethod
    async def _handle_start_current_group(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                        user: Any, chat: Any) -> None:
        """Handle start command in current group."""
        if chat.type not in GROUP_CHAT_TYPES:
            await update.message.reply_text("❌ Please provide a group ID or use this command in a group chat.\n\nUsage: `/init <group_id>`")
            return
        
        if not await AdminHandlers.is_admin(update, context):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Add current group to listening groups
        data_storage.add_listening_group(chat.id)
        
        # Log the action
        logger.info(f"Admin {user.first_name} (ID: {user.id}) started listening to group {chat.title} (ID: {chat.id})")
        print(f"🔊 Admin {user.first_name} started listening to group {chat.title} (ID: {chat.id})")
        
        # Send confirmation
        await update.message.reply_text(f"✅ Now listening to messages in {chat.title}")
    
    @staticmethod
    async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin command to stop listening to group chat."""
        user = update.effective_user
        chat = update.effective_chat
        
        if context.args:
            await AdminHandlers._handle_end_with_group_id(update, context, user, context.args[0])
        else:
            await AdminHandlers._handle_end_current_group(update, context, user, chat)
    
    @staticmethod
    async def _handle_end_with_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                       user: Any, group_id_str: str) -> None:
        """Handle end command with group ID argument."""
        try:
            target_group_id = int(group_id_str)
            target_chat = await context.bot.get_chat(target_group_id)
            
            # Check if user is admin in the target group
            try:
                chat_member = await context.bot.get_chat_member(target_group_id, user.id)
                if chat_member.status not in ADMIN_STATUSES:
                    await update.message.reply_text(f"❌ You are not an admin in the group: {target_chat.title}")
                    return
            except Exception:
                await update.message.reply_text("❌ Unable to verify your admin status in that group.")
                return
            
            # Remove group from listening groups
            if data_storage.is_listening_to_group(target_group_id):
                data_storage.remove_listening_group(target_group_id)
                
                # Log the action
                logger.info(f"Admin {user.first_name} (ID: {user.id}) stopped listening to group {target_chat.title} (ID: {target_group_id})")
                print(f"🔇 Admin {user.first_name} stopped listening to group {target_chat.title} (ID: {target_group_id})")
                
                # Send confirmation
                await update.message.reply_text(f"✅ Stopped listening to messages in {target_chat.title} (ID: {target_group_id})")
            else:
                await update.message.reply_text(f"❌ Not currently listening to {target_chat.title} (ID: {target_group_id})")
            
        except ValueError:
            await update.message.reply_text("❌ Invalid group ID. Please provide a valid number.")
        except Exception as e:
            await update.message.reply_text(f"❌ Unable to access group with ID: {group_id_str}. Make sure the bot is added to that group.")
            logger.error(f"Error accessing group {group_id_str}: {e}")
    
    @staticmethod
    async def _handle_end_current_group(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                       user: Any, chat: Any) -> None:
        """Handle end command in current group."""
        if chat.type not in GROUP_CHAT_TYPES:
            await update.message.reply_text("❌ Please provide a group ID or use this command in a group chat.\n\nUsage: `/end <group_id>`")
            return
        
        if not await AdminHandlers.is_admin(update, context):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Remove current group from listening groups
        if data_storage.is_listening_to_group(chat.id):
            data_storage.remove_listening_group(chat.id)
            
            # Log the action
            logger.info(f"Admin {user.first_name} (ID: {user.id}) stopped listening to group {chat.title} (ID: {chat.id})")
            print(f"🔇 Admin {user.first_name} stopped listening to group {chat.title} (ID: {chat.id})")
            
            # Send confirmation
            await update.message.reply_text(f"✅ Stopped listening to messages in {chat.title}")
        else:
            await update.message.reply_text(f"❌ Not currently listening to {chat.title}")


class UserHandlers:
    """Handles user-related commands."""
    
    @staticmethod
    async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle hello command."""
        user = update.effective_user
        logger.info(f"User {user.first_name} (ID: {user.id}) sent /hello command")
        print(f"👤 User {user.first_name} (ID: {user.id}) sent /hello command")
        
        response = f'hello {user.first_name}'
        await update.message.reply_text(response)
        
        logger.info(f"Bot responded to {user.first_name}: {response}")
        print(f"🤖 Bot responded to {user.first_name}: {response}")
    
    @staticmethod
    async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show points status for user by group."""
        user = update.effective_user
        chat = update.effective_chat
        
        if chat.type != PRIVATE_CHAT_TYPE:
            return
        
        group_name = ' '.join(context.args) if context.args else None
        status_text = data_storage.format_user_status(user.id, group_name)
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
        
        logger.info(f"User {user.first_name} (ID: {user.id}) requested status")
        print(f"📊 User {user.first_name} (ID: {user.id}) requested status")
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show all available commands."""
        user = update.effective_user
        chat = update.effective_chat
        
        help_text = HELP_TEXT
        
        if chat.type in GROUP_CHAT_TYPES:
            if data_storage.is_listening_to_group(chat.id):
                help_text += f"✅ Listening to messages in {chat.title}"
            else:
                help_text += f"❌ Not listening to messages in {chat.title}"
        else:
            help_text += "💬 This is a private chat"
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
        logger.info(f"User {user.first_name} (ID: {user.id}) requested help")
        print(f"❓ User {user.first_name} (ID: {user.id}) requested help")
    
    @staticmethod
    async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show current leaderboard for active events in the group."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Only work in groups where bot is listening
        if chat.type not in GROUP_CHAT_TYPES or not data_storage.is_listening_to_group(chat.id):
            await update.message.reply_text("❌ This command only works in groups where the bot is listening.")
            return
        
        # Check event status
        event_status = reward_system.get_event_status(chat.id)
        
        if event_status == "active":
            # Get current standings using the new method
            standings = reward_system.get_current_standings(chat.id)
            await update.message.reply_text(standings, parse_mode='Markdown')
        elif event_status == "not_started":
            config = reward_system.get_reward_config(chat.id)
            start_time = config.get('start_time')
            await update.message.reply_text(
                f"⏰ **Event Not Started Yet**\n\n"
                f"Event: {config.get('group_name', 'Unknown Group')}\n"
                f"Type: {config.get('type', 'unknown').title()}\n"
                f"Total Reward: {config.get('total_amount', 0)}\n\n"
                f"Event will begin at: {start_time.strftime(DATE_FORMAT)}\n"
                f"Use /result to see when the event starts!"
            )
        elif event_status == "finished":
            await update.message.reply_text(
                "🏁 **Event Finished**\n\n"
                "This event has already finished. Use /result to see the final results!"
            )
        else:
            await update.message.reply_text("🏁 No active events in this group. Ask an admin to start a reward event!")
        
        logger.info(f"User {user.first_name} (ID: {user.id}) requested leaderboard in {chat.title}")
        print(f"📊 User {user.first_name} requested leaderboard in {chat.title}")
    
    @staticmethod
    async def reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show current reward event information."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Only work in groups where bot is listening
        if chat.type not in GROUP_CHAT_TYPES or not data_storage.is_listening_to_group(chat.id):
            await update.message.reply_text("❌ This command only works in groups where the bot is listening.")
            return
        
        # Check event status
        event_status = reward_system.get_event_status(chat.id)
        
        if event_status == "active":
            # Get current standings using the new method
            standings = reward_system.get_current_standings(chat.id)
            await update.message.reply_text(standings, parse_mode='Markdown')
        elif event_status == "not_started":
            config = reward_system.get_reward_config(chat.id)
            start_time = config.get('start_time')
            await update.message.reply_text(
                f"⏰ **Event Not Started Yet**\n\n"
                f"Event: {config.get('group_name', 'Unknown Group')}\n"
                f"Type: {config.get('type', 'unknown').title()}\n"
                f"Total Reward: {config.get('total_amount', 0)}\n\n"
                f"Event will begin at: {start_time.strftime(DATE_FORMAT)}\n"
                f"Use /result to see when the event starts!"
            )
        elif event_status == "finished":
            await update.message.reply_text(
                "🏁 **Event Finished**\n\n"
                "This event has already finished. Use /result to see the final results!"
            )
        else:
            await update.message.reply_text("🏁 No active events in this group. Ask an admin to start a reward event!")
        
        logger.info(f"User {user.first_name} (ID: {user.id}) requested reward info in {chat.title}")
        print(f"🏆 User {user.first_name} requested reward info in {chat.title}")
    
    @staticmethod
    async def result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show current standings or final results for events."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Only work in groups where bot is listening
        if chat.type not in GROUP_CHAT_TYPES or not data_storage.is_listening_to_group(chat.id):
            await update.message.reply_text("❌ This command only works in groups where the bot is listening.")
            return
        
        # Check if there's an event configuration
        config = reward_system.get_reward_config(chat.id)
        if not config:
            await update.message.reply_text("🏁 No events configured in this group. Ask an admin to start a reward event!")
            return
        
        # Get detailed event status
        event_status = reward_system.get_event_status(chat.id)
        
        if event_status == "active":
            # Show current standings
            print("Event is active. Showing current standings")
            standings = reward_system.get_current_standings(chat.id)
            await update.message.reply_text(standings, parse_mode='Markdown')
        elif event_status == "finished":
            # Show final results
            print("Event finished. Showing final results")
            results = reward_system.get_event_results(chat.id)
            await update.message.reply_text(results)
        elif event_status == "not_started":
            # Event hasn't started yet
            start_time = config.get('start_time')
            current_time = datetime.now()
            time_until_start = start_time - current_time
            
            hours = int(time_until_start.total_seconds() // 3600)
            minutes = int((time_until_start.total_seconds() % 3600) // 60)
            
            if hours > 24:
                days = hours // 24
                hours = hours % 24
                time_text = f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                time_text = f"{hours}h {minutes}m"
            else:
                time_text = f"{minutes}m"
            
            await update.message.reply_text(
                f"⏰ **Event Not Started Yet**\n\n"
                f"Event: {config.get('group_name', 'Unknown Group')}\n"
                f"Type: {config.get('type', 'unknown').title()}\n"
                f"Total Reward: {config.get('total_amount', 0)}\n"
                f"Starts in: {time_text}\n\n"
                f"Event will begin at: {start_time.strftime(DATE_FORMAT)}"
            )
        elif event_status == "time_expired":
            # Event time has expired but status not updated yet
            await update.message.reply_text(
                f"🏁 **Event Time Expired**\n\n"
                f"Event: {config.get('group_name', 'Unknown Group')}\n"
                f"Type: {config.get('type', 'unknown').title()}\n"
                f"Total Reward: {config.get('total_amount', 0)}\n\n"
                f"Final results will be announced soon!"
            )
        else:
            await update.message.reply_text("🏁 No active events in this group. Ask an admin to start a reward event!")
        
        logger.info(f"User {user.first_name} (ID: {user.id}) requested results in {chat.title}")
        print(f"🏆 User {user.first_name} requested results in {chat.title}")


class ROFLHandlers:
    """Handles ROFL wallet-related commands."""
    
    @staticmethod
    async def new_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin command to create a new ROFL wallet."""
        user = update.effective_user
        
        # Verify admin status
        if not await AdminHandlers.is_admin(update, context):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        try:
            # Generate unique pool ID
            pool_id = f"pool_{int(time.time())}"
            
            # Generate wallet using ROFL
            wallet_info = rofl_service.generate_wallet(pool_id)
            
            # Store wallet info securely
            data_storage.store_wallet_info(wallet_info)
            
            # Display funding information
            message = f"""
🏦 **New ROFL Wallet Created**

💰 **Wallet Address**: `{wallet_info['address']}`
🔗 **Network**: Oasis Sapphire
📊 **Pool ID**: `{wallet_info['pool_id']}`
🆔 **ROFL App ID**: `{wallet_info['app_id']}`

💡 **Instructions**:
1. Send funds to the wallet address above
2. Use `/bot` to monitor balance
3. This wallet is secured by ROFL for maximum security

⚠️ **Security**: This wallet is managed by ROFL with attested execution
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
            logger.info(f"Admin {user.first_name} (ID: {user.id}) created new ROFL wallet")
            print(f"🏦 Admin {user.first_name} created new ROFL wallet: {wallet_info['address']}")
            
        except Exception as e:
            logger.error(f"Failed to create ROFL wallet: {e}")
            await update.message.reply_text(f"❌ Failed to create wallet: {str(e)}")
    
    @staticmethod
    async def bot_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display bot wallet information and balance."""
        user = update.effective_user
        
        try:
            # Get latest wallet info from storage
            wallet_info = data_storage.get_latest_wallet_info()
            
            if not wallet_info:
                await update.message.reply_text("❌ No wallet found. Ask an admin to create one with `/new_bot`.")
                return
            
            # Get current balance
            try:
                balance = rofl_service.get_wallet_balance(wallet_info['address'])
                balance_text = f"{balance:.6f} ROSE"
            except Exception as e:
                logger.error(f"Failed to get balance: {e}")
                balance_text = "Unable to fetch balance"
            
            # Format creation time
            from datetime import datetime
            created_time = datetime.fromtimestamp(wallet_info['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            
            message = f"""
🤖 **Bot Wallet Information**

📍 **Address**: `{wallet_info['address']}`
💎 **Balance**: {balance_text}
📊 **Pool ID**: `{wallet_info['pool_id']}`
🆔 **ROFL App ID**: `{wallet_info['app_id']}`
⏰ **Created**: {created_time}

💡 **To fund this wallet**:
Send ROSE tokens to the address above on Oasis Sapphire network.

🔒 **Security**: This wallet is secured by ROFL with attested execution.
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
            logger.info(f"User {user.first_name} (ID: {user.id}) requested bot wallet info")
            print(f"🤖 User {user.first_name} requested bot wallet info")
            
        except Exception as e:
            logger.error(f"Failed to get bot wallet info: {e}")
            await update.message.reply_text(f"❌ Failed to get wallet information: {str(e)}")


class BotHandlers:
    """Handles bot-related events."""
    
    @staticmethod
    async def init_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for when the bot is added to a group or its status changes."""
        chat_member = update.my_chat_member
        new_status = chat_member.new_chat_member.status
        old_status = chat_member.old_chat_member.status
        chat = chat_member.chat

        if new_status in ["member", "restricted"] and old_status == "left":
            logger.info(f"Bot added to group: {chat.title} (ID: {chat.id})")
            print(f"🤖 Bot added to group: {chat.title} (ID: {chat.id})")
            await context.bot.send_message(chat_id=chat.id, text=BOT_INIT_MESSAGE)
        elif new_status == "left" and old_status != "left":
            logger.info(f"Bot removed from group: {chat.title} (ID: {chat.id})")
            print(f"🤖 Bot removed from group: {chat.title} (ID: {chat.id})")


# Create handler instances
admin_handlers = AdminHandlers()
user_handlers = UserHandlers()
bot_handlers = BotHandlers()