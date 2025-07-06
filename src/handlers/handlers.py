"""
Command handlers module for the Telegram bot.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
from telegram import Update
from config.abi import reward_pool_abi
from telegram.ext import ContextTypes, ConversationHandler

from config.config import (
    CHOOSING_GROUP, CHOOSING_TYPE, ENTERING_POOL_AMOUNT, ENTERING_RANK_AMOUNT,
    ENTERING_RANK_DISTRIBUTION, ENTERING_START_TIME, ENTERING_END_TIME,
    ADMIN_STATUSES, GROUP_CHAT_TYPES, PRIVATE_CHAT_TYPE, HELP_TEXT, DATE_FORMAT,
    REWARD_TYPE_POOL, REWARD_TYPE_RANK, BOT_INIT_MESSAGE, CONTRACT_ADDRESS, DEFAULT_POOL_AMOUNT
)
from services.data_storage import data_storage
from services.reward_system import reward_system
from services.rofl_service import rofl_service
from utils.verification import verification, VerificationRule

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

    @staticmethod
    async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Test command to get ROFL app ID."""
        user = update.effective_user
        
        try:
            # Get app ID directly from ROFL service
            app_id = rofl_service.get_app_id()
            
            message = f"""
🧪 **ROFL App ID Test**

🆔 **App ID**: `{app_id}`
🔗 **Status**: {'✅ Connected' if app_id != 'unknown' else '❌ Not Connected'}
⏰ **Timestamp**: {int(time.time())}

💡 **This command tests the ROFL service connection and retrieves the current app identifier.**
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
            logger.info(f"User {user.first_name} (ID: {user.id}) tested ROFL app ID: {app_id}")
            print(f"🧪 User {user.first_name} tested ROFL app ID: {app_id}")
            
        except Exception as e:
            logger.error(f"Failed to get ROFL app ID: {e}")
            await update.message.reply_text(f"❌ Failed to get ROFL app ID: {str(e)}")


class VerificationHandlers:
    """Handles verification-related commands."""
    
    @staticmethod
    async def set_rule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Admin command to set verification rules for a group."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Only work in private chat
        if chat.type != PRIVATE_CHAT_TYPE:
            await update.message.reply_text("❌ This command only works in private chat.")
            return
        
        # If user provided group ID directly, use it
        if context.args:
            try:
                group_id = int(context.args[0])
                await VerificationHandlers._verify_admin_and_start_rule_setting(update, context, user, group_id)
                return
            except ValueError:
                await update.message.reply_text("❌ Invalid group ID. Please provide a valid number.")
                return
        
        # Get groups where user is admin
        admin_groups = await VerificationHandlers._get_user_admin_groups(context, user.id)
        
        if not admin_groups:
            await update.message.reply_text(
                "👑 **No Admin Groups Found**\n\n"
                "You're not an admin in any groups where the bot is present, or the bot cannot access those groups.\n\n"
                "To use this command:\n"
                "• Make sure you're an admin in a group\n"
                "• Add the bot to that group\n"
                "• Try again with `/set_rule <group_id>` if needed"
            )
            return
        
        # Show groups for admin to pick
        context.user_data['selecting_group_for_rule_setting'] = True
        context.user_data['available_admin_groups'] = admin_groups
        
        group_list = ""
        for i, (group_id, group_name, admin_role, has_rules) in enumerate(admin_groups, 1):
            rule_status = "📝 Has rules" if has_rules else "🆕 No rules set"
            group_list += f"{i}. **{group_name}** - {admin_role} - {rule_status}\n"
        
        await update.message.reply_text(
            f"👑 **Select Group to Set Rules**\n\n"
            f"I found you as admin in these groups:\n\n{group_list}\n"
            f"Reply with the number (1-{len(admin_groups)}) to set verification rules for that group:"
        )
    
    @staticmethod
    async def _get_user_admin_groups(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> list:
        """Get groups where user is admin and bot has access."""
        admin_groups = []
        
        # We need to check groups where the bot exists and user might be admin
        # Since we can't enumerate all groups, we'll check groups that have rules or listening status
        checked_groups = set()
        
        # Check groups with verification rules
        for group_id in verification.group_rules.keys():
            checked_groups.add(group_id)
        
        # Check groups where bot is listening
        listening_groups = data_storage.get_listening_groups()
        for group_id in listening_groups:
            checked_groups.add(group_id)
        
        # Check each group for admin status
        for group_id in checked_groups:
            try:
                # Check if user is admin in this group
                chat_member = await context.bot.get_chat_member(group_id, user_id)
                if chat_member.status in ADMIN_STATUSES:
                    # Get group info
                    try:
                        group_chat = await context.bot.get_chat(group_id)
                        group_name = group_chat.title
                    except Exception:
                        group_name = f"Group {group_id}"
                    
                    # Determine admin role
                    admin_role = "👑 Owner" if chat_member.status == "creator" else "🛡️ Admin"
                    
                    # Check if group has rules
                    has_rules = verification.has_group_rule(group_id)
                    
                    admin_groups.append((group_id, group_name, admin_role, has_rules))
            except Exception:
                # User not admin or error accessing group
                continue
        
        return admin_groups
    
    @staticmethod
    async def _verify_admin_and_start_rule_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                                  user: Any, group_id: int) -> None:
        """Verify admin status and start rule setting for specific group."""
        try:
            chat_member = await context.bot.get_chat_member(group_id, user.id)
            if chat_member.status not in ADMIN_STATUSES:
                await update.message.reply_text("❌ You are not an admin in that group.")
                return
        except Exception:
            await update.message.reply_text("❌ Unable to verify your admin status in that group.")
            return
        
        # Start the rule setting process
        await VerificationHandlers._start_rule_setting(update, context, group_id)
    
    @staticmethod
    async def handle_admin_group_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle admin group selection for rule setting."""
        text = update.message.text.strip()
        
        available_groups = context.user_data.get('available_admin_groups', [])
        
        try:
            selection = int(text)
            if 1 <= selection <= len(available_groups):
                group_id, group_name, admin_role, has_rules = available_groups[selection - 1]
                
                # Clean up group selection state
                context.user_data.pop('selecting_group_for_rule_setting', None)
                context.user_data.pop('available_admin_groups', None)
                
                await update.message.reply_text(
                    f"👑 **Setting Rules for {group_name}**\n\n"
                    f"Your role: {admin_role}\n"
                    f"Current status: {'📝 Has existing rules' if has_rules else '🆕 No rules set'}\n\n"
                    f"Starting rule configuration..."
                )
                
                await VerificationHandlers._start_rule_setting(update, context, group_id)
            else:
                await update.message.reply_text(f"❌ Please enter a number between 1 and {len(available_groups)}:")
        except ValueError:
            await update.message.reply_text(f"❌ Please enter a valid number between 1 and {len(available_groups)}:")
    
    @staticmethod
    async def _start_rule_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 group_id: int) -> None:
        """Start the rule setting process."""
        # Store the group_id in context for later use
        context.user_data['setting_rule_for_group'] = group_id
        context.user_data['verification_step'] = 'country'
        context.user_data['rule_data'] = {}
        
        await update.message.reply_text(
            "🔧 **Setting Verification Rules**\n\n"
            "I'll collect all verification requirements in one go. "
            "You can type 'None' to skip any requirement.\n\n"
            "Please provide your requirements in this format:\n"
            "**Country: [country name or None]**\n"
            "**Age: [minimum age or None]**\n"
            "**NFT: [Penguin/Ape or None]**\n\n"
            "Example: Country: USA, Age: 18, NFT: Penguin\n"
            "Or: Country: None, Age: 21, NFT: None"
        )
    
    @staticmethod
    async def handle_rule_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle rule setting conversation."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Only work in private chat
        if chat.type != PRIVATE_CHAT_TYPE:
            return
        
        # Check if user is in rule setting mode
        if 'setting_rule_for_group' not in context.user_data:
            return
        
        text = update.message.text.strip()
        
        # Parse the input format: Country: X, Age: Y, NFT: Z
        try:
            # Split by comma and parse each part
            parts = [part.strip() for part in text.split(',')]
            rule_data = {}
            
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'country':
                        rule_data['country'] = value if value.lower() != 'none' else None
                    elif key == 'age':
                        if value.lower() != 'none':
                            try:
                                age = int(value)
                                rule_data['age'] = age if age >= 0 else None
                            except ValueError:
                                rule_data['age'] = None
                        else:
                            rule_data['age'] = None
                    elif key == 'nft':
                        if value.lower() in ['penguin']:
                            rule_data['nft_holder'] = 'penguin'
                        elif value.lower() in ['ape']:
                            rule_data['nft_holder'] = 'ape'
                        else:
                            rule_data['nft_holder'] = None
            
            # Save parsed data
            context.user_data['rule_data'] = rule_data
            await VerificationHandlers._save_rule(update, context, user)
            
        except Exception as e:
            await update.message.reply_text(
                "❌ Invalid format. Please use:\n"
                "Country: [name or None], Age: [number or None], NFT: [Penguin/Ape or None]\n\n"
                "Example: Country: USA, Age: 18, NFT: Penguin"
            )
    
    @staticmethod
    async def _save_rule(update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any) -> None:
        """Save the verification rule."""
        group_id = context.user_data['setting_rule_for_group']
        rule_data = context.user_data['rule_data']
        
        # Create the rule
        rule = VerificationRule(
            country=rule_data.get('country'),
            age=rule_data.get('age'),
            nft_holder=rule_data.get('nft_holder'),
            collect_address=rule_data.get('collect_address', True)
        )
        
        # Save the rule
        verification.set_group_rule(group_id, rule)
        
        # Get group info
        try:
            group_chat = await context.bot.get_chat(group_id)
            group_name = group_chat.title
        except Exception:
            group_name = f"Group {group_id}"
        
        # Create summary message
        summary = f"✅ **Verification Rule Set for {group_name}**\n\n"
        summary += verification.get_verification_requirements_text(group_id)
        
        await update.message.reply_text(summary)
        
        # Execute smart contract transaction after setting the rule
        try:
            await update.message.reply_text("🔗 Creating reward pool on-chain...")
            
            # Smart contract configuration
            contract_address = CONTRACT_ADDRESS 
            
            # Create Web3 instance for ABI encoding
            from web3 import Web3
            w3 = Web3()
            
            # Create contract instance
            contract = w3.eth.contract(abi=reward_pool_abi)
            
            # Prepare function parameters for createPool
            pool_name = f"Group_{group_id}_Pool"
            start_time = int(time.time())  # Current timestamp
            end_time = start_time + (7 * 24 * 60 * 60)  # 7 days from now
            
            function_params = [
                pool_name,
                start_time,
                end_time
            ]
            
            # Encode function call
            function_data = contract.encodeABI(
                fn_name='createPool',
                args=function_params
            )
            
            # Convert ROSE amount to wei (1 ROSE = 10^18 wei)
            amount_wei = int(DEFAULT_POOL_AMOUNT * 10**18)
            
            # Submit authenticated transaction via ROFL
            # This will be signed by the ROFL app's endorsed key
            tx_result = rofl_service.submit_authenticated_tx(
                to_address=contract_address,
                data=function_data,
                value=amount_wei
            )
            
            # Report transaction success
            if tx_result:
                await update.message.reply_text(
                    f"🎉 **Reward Pool Created Successfully!**\n\n"
                    f"Group: {group_name}\n"
                    f"Pool Name: `{pool_name}`\n"
                    f"💰 **Amount Funded**: {DEFAULT_POOL_AMOUNT} ROSE\n"
                    f"Contract: `{contract_address}`\n"
                    f"Function: `createPool`\n"
                    f"Start Time: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"End Time: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Transaction Hash: `{tx_result.get('hash', 'N/A')}`\n"
                    f"Status: {'✅ Success' if tx_result.get('status') == 'success' else '⏳ Pending'}\n\n"
                    f"The reward pool has been created and funded on-chain via ROFL smart contract."
                )
            else:
                await update.message.reply_text("⚠️ Transaction submitted but no confirmation received.")
                
        except Exception as e:
            logger.error(f"Error executing smart contract transaction after rule setting: {e}")
            await update.message.reply_text(
                f"⚠️ **Smart Contract Transaction Failed**\n\n"
                f"The verification rule was saved locally but could not be recorded on-chain.\n"
                f"Error: {str(e)}\n\n"
                f"The rule is still active and functional."
            )
        
        # Clean up context
        context.user_data.pop('setting_rule_for_group', None)
        context.user_data.pop('verification_step', None)
        context.user_data.pop('rule_data', None)
        
        logger.info(f"Admin {user.first_name} (ID: {user.id}) set verification rule for group {group_id}")
        print(f"🔧 Admin {user.first_name} set verification rule for group {group_id}")
    
    @staticmethod
    async def verify_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle user verification process."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Only work in private chat
        if chat.type != PRIVATE_CHAT_TYPE:
            await update.message.reply_text("❌ This command only works in private chat.")
            return
        
        # If user provided group ID directly, use it
        if context.args:
            try:
                group_id = int(context.args[0])
                await VerificationHandlers._start_verification_for_group(update, context, user, group_id)
                return
            except ValueError:
                await update.message.reply_text("❌ Invalid group ID. Please provide a valid number.")
                return
        
        # Get groups the user is in that have verification rules
        user_groups = await VerificationHandlers._get_user_groups_with_rules(context, user.id)
        
        if not user_groups:
            await update.message.reply_text(
                "📝 **No Verification Needed**\n\n"
                "You're not in any groups that require verification, or none of your groups have verification rules set up yet."
            )
            return
        
        # Show groups for user to pick
        context.user_data['selecting_group_for_verification'] = True
        context.user_data['available_groups'] = user_groups
        
        group_list = ""
        for i, (group_id, group_name, has_rules) in enumerate(user_groups, 1):
            status = "🔐 Requires verification" if has_rules else "✅ No verification needed"
            group_list += f"{i}. **{group_name}** - {status}\n"
        
        await update.message.reply_text(
            f"🔍 **Select Group for Verification**\n\n"
            f"I found you in these groups:\n\n{group_list}\n"
            f"Reply with the number (1-{len(user_groups)}) to select a group for verification:"
        )
    
    @staticmethod
    async def _get_user_groups_with_rules(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> list:
        """Get groups the user is in that have verification rules."""
        user_groups = []
        
        # Check all groups that have verification rules
        for group_id in verification.group_rules.keys():
            try:
                # Check if user is member of this group
                chat_member = await context.bot.get_chat_member(group_id, user_id)
                if chat_member.status in ['member', 'administrator', 'creator']:
                    # Get group info
                    try:
                        group_chat = await context.bot.get_chat(group_id)
                        group_name = group_chat.title
                    except Exception:
                        group_name = f"Group {group_id}"
                    
                    has_rules = verification.has_group_rule(group_id)
                    user_groups.append((group_id, group_name, has_rules))
            except Exception:
                # User not in group or error accessing group
                continue
        
        # Also check listening groups in case user is in groups without rules yet
        listening_groups = data_storage.get_listening_groups()
        for group_id in listening_groups:
            try:
                # Check if user is member of this group and not already in list
                if not any(g[0] == group_id for g in user_groups):
                    chat_member = await context.bot.get_chat_member(group_id, user_id)
                    if chat_member.status in ['member', 'administrator', 'creator']:
                        # Get group info
                        try:
                            group_chat = await context.bot.get_chat(group_id)
                            group_name = group_chat.title
                        except Exception:
                            group_name = f"Group {group_id}"
                        
                        has_rules = verification.has_group_rule(group_id)
                        user_groups.append((group_id, group_name, has_rules))
            except Exception:
                # User not in group or error accessing group
                continue
        
        return user_groups
    
    @staticmethod
    async def _start_verification_for_group(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                          user: Any, group_id: int) -> None:
        """Start verification process for a specific group."""
        # Check if group has verification rules
        if not verification.has_group_rule(group_id):
            await update.message.reply_text("✅ This group has no verification requirements. You're all set!")
            return
        
        # Get group info
        try:
            group_chat = await context.bot.get_chat(group_id)
            group_name = group_chat.title
        except Exception:
            group_name = f"Group {group_id}"
        
        # Show requirements and start verification
        requirements_text = verification.get_verification_requirements_text(group_id)
        
        await update.message.reply_text(
            f"🔍 **Verification for {group_name}**\n\n"
            f"{requirements_text}\n\n"
            "Let's start the verification process. I'll ask you some questions."
        )
        
        # Start verification process
        verification.start_verification_process(user.id, group_id)
        context.user_data['verifying_for_group'] = group_id
        
        # Ask first question
        await VerificationHandlers._ask_verification_question(update, user)
    
    @staticmethod
    async def handle_group_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle group selection for verification."""
        user = update.effective_user
        text = update.message.text.strip()
        
        available_groups = context.user_data.get('available_groups', [])
        
        try:
            selection = int(text)
            if 1 <= selection <= len(available_groups):
                group_id, group_name, has_rules = available_groups[selection - 1]
                
                # Clean up group selection state
                context.user_data.pop('selecting_group_for_verification', None)
                context.user_data.pop('available_groups', None)
                
                if has_rules:
                    await VerificationHandlers._start_verification_for_group(update, context, user, group_id)
                else:
                    await update.message.reply_text(f"✅ **{group_name}** has no verification requirements. You're all set!")
            else:
                await update.message.reply_text(f"❌ Please enter a number between 1 and {len(available_groups)}:")
        except ValueError:
            await update.message.reply_text(f"❌ Please enter a valid number between 1 and {len(available_groups)}:")
    
    @staticmethod
    async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle verification conversation."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Only work in private chat
        if chat.type != PRIVATE_CHAT_TYPE:
            return
        
        # Check if user is in verification mode
        if 'verifying_for_group' not in context.user_data:
            return
        
        pending = verification.get_pending_verification(user.id)
        if not pending:
            return
        
        step = pending['step']
        text = update.message.text.strip()
        group_id = pending['group_id']
        rule = verification.get_group_rule(group_id)
        
        if step == 'country':
            # Handle country input (mock version - accept any input matching user's name)
            if rule.country and rule.country != "None":
                verification.update_verification_data(user.id, 'country', text)
                
                # Mock version: accept if user enters their first name
                if text.lower() == user.first_name.lower():
                    await update.message.reply_text("✅ Country verified!")
                else:
                    await update.message.reply_text(f"❌ For mock version, please enter your name '{user.first_name}' to pass:")
                    return
            
            # Move to next step
            if rule.age and rule.age > 0:
                verification.advance_verification_step(user.id, 'age')
                await update.message.reply_text(f"What is your age? (Must be at least {rule.age})")
            elif rule.nft_holder is not None:
                verification.advance_verification_step(user.id, 'wallet_address')
                await update.message.reply_text(f"Please provide your wallet address to verify {rule.nft_holder} NFT ownership:")
            elif rule.collect_address:
                verification.advance_verification_step(user.id, 'wallet_address')
                await update.message.reply_text("Please provide your wallet address for future rewards:")
            else:
                await VerificationHandlers._complete_verification(update, context, user)
        
        elif step == 'age':
            # Handle age input (mock version - accept if user enters their name)
            try:
                # Mock version: accept if user enters their first name instead of age
                if text.lower() == user.first_name.lower():
                    age = rule.age  # Set to minimum required age
                    verification.update_verification_data(user.id, 'age', age)
                    await update.message.reply_text("✅ Age verified!")
                else:
                    await update.message.reply_text(f"❌ For mock version, please enter your name '{user.first_name}' to pass:")
                    return
                    
            except Exception:
                await update.message.reply_text(f"❌ For mock version, please enter your name '{user.first_name}' to pass:")
                return
            
            # Move to next step
            if rule.nft_holder is not None:
                verification.advance_verification_step(user.id, 'wallet_address')
                await update.message.reply_text(f"Please provide your wallet address to verify {rule.nft_holder} NFT ownership:")
            elif rule.collect_address:
                verification.advance_verification_step(user.id, 'wallet_address')
                await update.message.reply_text("Please provide your wallet address for future rewards:")
            else:
                await VerificationHandlers._complete_verification(update, context, user)
        
        
        elif step == 'wallet_address':
            # Handle wallet address input
            address = text.strip()
            
            # Basic validation for wallet address
            if len(address) < 10:
                await update.message.reply_text("❌ Please enter a valid wallet address:")
                return
            
            # Validate Ethereum address format
            try:
                from web3 import Web3
                Web3.to_checksum_address(address)
            except Exception:
                await update.message.reply_text(
                    "❌ Invalid Ethereum address format.\n\n"
                    "Please ensure your address:\n"
                    "• Starts with '0x'\n"
                    "• Is exactly 42 characters long\n"
                    "• Contains only valid hexadecimal characters\n\n"
                    "Example: `0x742d35Cc6634C0532925a3b8D499d12A13639D36`"
                )
                return
            
            verification.update_verification_data(user.id, 'address', address)
            await update.message.reply_text("✅ Wallet address recorded!")
            
            # If NFT verification is required, check it now
            if rule.nft_holder is not None:
                await update.message.reply_text(f"🔍 Checking {rule.nft_holder} NFT ownership on Ethereum mainnet...")
                
                try:
                    # Import NFT service
                    from services.nft_service import nft_service
                    
                    # Check NFT ownership
                    nft_verified = nft_service.verify_nft_requirement(address, rule.nft_holder)
                    
                    if nft_verified:
                        await update.message.reply_text(f"✅ {rule.nft_holder.title()} NFT ownership verified on-chain!")
                        verification.update_verification_data(user.id, 'nft_holder', rule.nft_holder)
                    else:
                        # Show NFT summary for debugging
                        nft_summary = nft_service.get_nft_summary(address)
                        summary_text = "\n".join([f"• {nft.title()}: {count}" for nft, count in nft_summary.items()])
                        
                        # Get contract info for better error message
                        contract_info = nft_service.get_contract_info(rule.nft_holder)
                        contract_name = contract_info['name'] if contract_info else f"{rule.nft_holder.title()} NFT"
                        contract_address = contract_info['address'] if contract_info else "unknown"
                        
                        await update.message.reply_text(
                            f"❌ No {rule.nft_holder} NFTs found in your wallet.\n\n"
                            f"**Required:** {contract_name}\n"
                            f"**Contract:** `{contract_address}`\n\n"
                            f"**Your NFT holdings:**\n{summary_text}\n\n"
                            f"Please ensure your wallet contains at least one {rule.nft_holder} NFT."
                        )
                        return
                        
                except Exception as e:
                    logger.error(f"Error during NFT verification: {e}")
                    await update.message.reply_text(
                        f"⚠️ Unable to verify {rule.nft_holder} NFT ownership due to blockchain connectivity issues.\n\n"
                        f"Please try again later or contact support if the issue persists."
                    )
                    return
            
            # Complete verification
            await VerificationHandlers._complete_verification(update, context, user)
    
    @staticmethod
    async def _ask_verification_question(update: Update, user: Any) -> None:
        """Ask the first verification question."""
        pending = verification.get_pending_verification(user.id)
        if not pending:
            return
        
        group_id = pending['group_id']
        rule = verification.get_group_rule(group_id)
        
        if rule.country and rule.country != "None":
            await update.message.reply_text(f"What is your country? (Must be {rule.country})")
        elif rule.age and rule.age > 0:
            verification.advance_verification_step(user.id, 'age')
            await update.message.reply_text(f"What is your age? (Must be at least {rule.age})")
        elif rule.nft_holder is not None:
            verification.advance_verification_step(user.id, 'wallet_address')
            await update.message.reply_text(f"Please provide your wallet address to verify {rule.nft_holder} NFT ownership:")
        elif rule.collect_address:
            verification.advance_verification_step(user.id, 'wallet_address')
            await update.message.reply_text("Please provide your wallet address for future rewards:")
        else:
            await update.message.reply_text("✅ No verification needed!")
    
    @staticmethod
    async def _complete_verification(update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any) -> None:
        """Complete the verification process."""
        passed = verification.complete_verification(user.id)
        
        if passed:
            # Get group info for notification
            group_id = context.user_data.get('verifying_for_group')
            if group_id:
                try:
                    group_chat = await context.bot.get_chat(group_id)
                    group_name = group_chat.title
                    
                    # Send notification to group
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=f"🎉 {user.first_name} has successfully completed verification and can now participate in group activities!"
                    )
                except Exception as e:
                    logger.error(f"Failed to send group notification: {e}")
            
            await update.message.reply_text(
                "🎉 **Verification Successful!**\n\n"
                "You have successfully passed all verification requirements. "
                "You can now participate in the group! A notification has been sent to the group."
            )
        else:
            await update.message.reply_text(
                "❌ **Verification Failed**\n\n"
                "You did not meet all the verification requirements. "
                "Please contact the group admin if you think this is an error."
            )
        
        # Clean up context
        context.user_data.pop('verifying_for_group', None)
        
        logger.info(f"User {user.first_name} (ID: {user.id}) completed verification: {'passed' if passed else 'failed'}")
        print(f"🔍 User {user.first_name} verification: {'passed' if passed else 'failed'}")
    
    @staticmethod
    async def _show_verification_help_with_groups(update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any) -> None:
        """Show verification help with available groups."""
        # Get groups the user is in
        user_groups = await VerificationHandlers._get_user_groups_with_rules(context, user.id)
        
        if not user_groups:
            await update.message.reply_text(
                "🔍 **User Verification**\n\n"
                "❌ **No Groups Available**\n\n"
                "You're not in any groups that require verification yet. "
                "Join a group where the bot is active and try again.\n\n"
                "If you know the group ID, you can use:\n"
                "`/verify Country: [country], Age: [age], NFT: [Penguin/Ape/None], Group: [group_id]`"
            )
            return
        
        # Create group selection message
        group_list = "🔍 **Available Groups for Verification**\n\n"
        group_list += "Choose a group by typing the number, or use the format below:\n\n"
        
        for i, (group_id, group_name, has_rules) in enumerate(user_groups, 1):
            rule_info = "🔐 Requires verification" if has_rules else "✅ No verification needed"
            group_list += f"{i}. **{group_name}** - {rule_info}\n"
            group_list += f"   ID: `{group_id}`\n\n"
        
        group_list += "**Option 1: Quick Selection**\n"
        group_list += f"Reply with a number (1-{len(user_groups)}) to select a group\n\n"
        
        group_list += "**Option 2: Direct Format**\n"
        group_list += "`/verify Country: [country], Age: [age], NFT: [Penguin/Ape/None], Group: [group_id]`\n\n"
        
        group_list += "**Example:**\n"
        group_list += f"`/verify Country: USA, Age: 25, NFT: Penguin, Group: {user_groups[0][0]}`"
        
        # Store available groups for selection
        context.user_data['available_groups_for_verification'] = user_groups
        context.user_data['awaiting_group_selection_for_verification'] = True
        
        await update.message.reply_text(group_list)
    
    @staticmethod
    async def handle_group_selection_for_verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle group selection for verification when user chooses a number."""
        user = update.effective_user
        text = update.message.text.strip()
        
        available_groups = context.user_data.get('available_groups_for_verification', [])
        
        try:
            selection = int(text)
            if 1 <= selection <= len(available_groups):
                group_id, group_name, has_rules = available_groups[selection - 1]
                
                # Clean up selection state
                context.user_data.pop('awaiting_group_selection_for_verification', None)
                context.user_data.pop('available_groups_for_verification', None)
                
                # Check if group has rules
                if has_rules:
                    # Show requirements and ask for verification data
                    requirements_text = verification.get_verification_requirements_text(group_id)
                    
                    await update.message.reply_text(
                        f"🔍 **Selected: {group_name}**\n\n"
                        f"{requirements_text}\n\n"
                        "Now provide your verification information in this format:\n"
                        "`Country: [country], Age: [age], NFT: [Penguin/Ape/None]`\n\n"
                        "Example: `Country: USA, Age: 25, NFT: Penguin`"
                    )
                    
                    # Set up verification data collection
                    context.user_data['collecting_verification_data_for_group'] = group_id
                    context.user_data['target_group_name'] = group_name
                else:
                    await update.message.reply_text(f"✅ **{group_name}** has no verification requirements. You're all set!")
            else:
                await update.message.reply_text(f"❌ Please enter a number between 1 and {len(available_groups)}:")
        except ValueError:
            await update.message.reply_text(f"❌ Please enter a valid number between 1 and {len(available_groups)}:")
    
    @staticmethod
    async def handle_verification_data_collection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle collecting verification data after group selection."""
        user = update.effective_user
        text = update.message.text.strip()
        
        group_id = context.user_data.get('collecting_verification_data_for_group')
        group_name = context.user_data.get('target_group_name', f"Group {group_id}")
        
        # Parse the input format: Country: X, Age: Y, NFT: Z
        try:
            # Split by comma and parse each part
            parts = [part.strip() for part in text.split(',')]
            user_data = {}
            
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'country':
                        user_data['country'] = value
                    elif key == 'age':
                        try:
                            user_data['age'] = int(value)
                        except ValueError:
                            await update.message.reply_text("❌ Age must be a number.")
                            return
                    elif key == 'nft':
                        user_data['nft'] = value if value.lower() != 'none' else None
            
            # Store the user data with group ID
            user_data['group_id'] = group_id
            data_storage.store_user_registration_data(user.id, user_data)
            
            # Show collected data
            collected_data = f"📝 **Data Collected for {group_name}:**\n"
            collected_data += f"• Country: {user_data.get('country', 'Not provided')}\n"
            collected_data += f"• Age: {user_data.get('age', 'Not provided')}\n"
            collected_data += f"• NFT: {user_data.get('nft', 'None')}\n\n"
            
            await update.message.reply_text(collected_data + "Starting verification process...")
            
            # Clean up collection state
            context.user_data.pop('collecting_verification_data_for_group', None)
            context.user_data.pop('target_group_name', None)
            
            # Start verification process
            await VerificationHandlers._start_verification_for_group(update, context, user, group_id)
            
        except Exception as e:
            logger.error(f"Error processing verification data: {e}")
            await update.message.reply_text(
                "❌ Invalid format. Please use:\n"
                "`Country: [country], Age: [age], NFT: [Penguin/Ape/None]`\n\n"
                "Example: `Country: USA, Age: 25, NFT: Penguin`"
            )
    
    @staticmethod
    async def verify_with_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Combined command to collect user data and start verification."""
        user = update.effective_user
        chat = update.effective_chat
        
        # Only work in private chat
        if chat.type != PRIVATE_CHAT_TYPE:
            await update.message.reply_text("❌ This command only works in private chat.")
            return
        
        # Check if user provided all data in format: Country: X, Age: Y, NFT: Z, Group: ID
        if not context.args:
            # Show available groups instead of requiring group ID
            await VerificationHandlers._show_verification_help_with_groups(update, context, user)
            return
        
        # Parse the input
        text = ' '.join(context.args)
        try:
            # Split by comma and parse each part
            parts = [part.strip() for part in text.split(',')]
            user_data = {}
            
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'country':
                        user_data['country'] = value
                    elif key == 'age':
                        try:
                            user_data['age'] = int(value)
                        except ValueError:
                            await update.message.reply_text("❌ Age must be a number.")
                            return
                    elif key == 'nft':
                        user_data['nft'] = value if value.lower() != 'none' else None
                    elif key == 'group':
                        try:
                            user_data['group_id'] = int(value)
                        except ValueError:
                            await update.message.reply_text("❌ Group ID must be a number.")
                            return
            
            # Validate required fields
            if 'group_id' not in user_data:
                await update.message.reply_text("❌ Group ID is required.")
                return
            
            group_id = user_data['group_id']
            
            # Check if group has verification rules
            if not verification.has_group_rule(group_id):
                await update.message.reply_text("✅ This group has no verification requirements. You're all set!")
                return
            
            # Store user data
            data_storage.store_user_registration_data(user.id, user_data)
            
            # Get group info
            try:
                group_chat = await context.bot.get_chat(group_id)
                group_name = group_chat.title
            except Exception:
                group_name = f"Group {group_id}"
            
            # Show collected data and start verification
            collected_data = f"📝 **Registration Data Collected:**\n"
            collected_data += f"• Country: {user_data.get('country', 'Not provided')}\n"
            collected_data += f"• Age: {user_data.get('age', 'Not provided')}\n"
            collected_data += f"• NFT: {user_data.get('nft', 'None')}\n"
            collected_data += f"• Group: {group_name}\n\n"
            
            await update.message.reply_text(collected_data + "Now starting verification process...")
            
            # Start verification automatically
            await VerificationHandlers._start_verification_for_group(update, context, user, group_id)
            
        except Exception as e:
            await update.message.reply_text(
                "❌ Invalid format. Please use:\n"
                "`/verify Country: [country], Age: [age], NFT: [Penguin/Ape/None], Group: [group_id]`"
            )


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
verification_handlers = VerificationHandlers()