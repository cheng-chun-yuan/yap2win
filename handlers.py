"""
Command handlers module for the Telegram bot.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config import (
    CHOOSING_GROUP, CHOOSING_TYPE, ENTERING_POOL_AMOUNT, ENTERING_RANK_AMOUNT,
    ENTERING_RANK_DISTRIBUTION, ENTERING_START_TIME, ENTERING_END_TIME,
    ADMIN_STATUSES, GROUP_CHAT_TYPES, PRIVATE_CHAT_TYPE, HELP_TEXT, DATE_FORMAT,
    REWARD_TYPE_POOL, REWARD_TYPE_RANK, BOT_INIT_MESSAGE
)
from data_storage import data_storage
from reward_system import reward_system

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
            await update.message.reply_text("❌ Please provide a group ID or use this command in a group chat.\n\nUsage: `/start <group_id>`")
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