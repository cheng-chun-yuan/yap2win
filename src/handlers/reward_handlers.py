"""
Reward system command handlers for the Telegram bot.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config.config import (
    CHOOSING_GROUP, CHOOSING_TYPE, ENTERING_POOL_AMOUNT, ENTERING_RANK_AMOUNT,
    ENTERING_RANK_DISTRIBUTION, ENTERING_START_TIME, ENTERING_END_TIME,
    ADMIN_STATUSES, PRIVATE_CHAT_TYPE, DATE_FORMAT,
    REWARD_TYPE_POOL, REWARD_TYPE_RANK
)
from services.data_storage import data_storage
from services.reward_system import reward_system

logger = logging.getLogger(__name__)


class RewardHandlers:
    """Handles reward-related commands."""
    
    @staticmethod
    async def set_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Admin command to set reward configuration - only works in private chat."""
        user = update.effective_user
        chat = update.effective_chat
        
        if chat.type != PRIVATE_CHAT_TYPE:
            return ConversationHandler.END
        
        admin_groups = await RewardHandlers._get_admin_groups(user, context)
        
        if not admin_groups:
            await update.message.reply_text("❌ You need to be an admin in at least one group where the bot is listening to set rewards.")
            return ConversationHandler.END
        
        groups_text = RewardHandlers._format_groups_text(admin_groups)
        context.user_data['admin_groups'] = admin_groups
        
        # Handle both message and callback query updates
        if update.message:
            await update.message.reply_text(groups_text, parse_mode='Markdown')
        elif update.callback_query:
            await update.callback_query.edit_message_text(groups_text, parse_mode='Markdown')
        else:
            # Fallback: try to send a new message
            await context.bot.send_message(chat_id=update.effective_chat.id, text=groups_text, parse_mode='Markdown')
        return CHOOSING_GROUP
    
    @staticmethod
    async def _get_admin_groups(user: Any, context: ContextTypes.DEFAULT_TYPE) -> List[Tuple[int, str]]:
        """Get groups where user is admin and bot is listening."""
        admin_groups = []
        for group_id in data_storage.get_listening_groups():
            try:
                chat_member = await context.bot.get_chat_member(group_id, user.id)
                if chat_member.status in ADMIN_STATUSES:
                    group_info = await context.bot.get_chat(group_id)
                    admin_groups.append((group_id, group_info.title))
            except Exception:
                continue
        return admin_groups
    
    @staticmethod
    def _format_groups_text(admin_groups: List[Tuple[int, str]]) -> str:
        """Format the groups selection text."""
        groups_text = "🏆 Set Reward Configuration\n\n"
        groups_text += "Available groups where you are admin:\n\n"
        
        for i, (group_id, group_name) in enumerate(admin_groups, 1):
            current_config = reward_system.get_reward_config(group_id)
            config_type = current_config.get('type', 'None') if current_config else 'None'
            total_amount = current_config.get('total_amount', 0) if current_config else 0
            
            groups_text += f"{i}. {group_name} (ID: {group_id})\n"
            if config_type != 'None':
                groups_text += f"   └ Current: {config_type.title()} reward - {total_amount}\n"
            else:
                groups_text += f"   └ No reward set\n"
        
        groups_text += "\nReply with the number of the group you want to configure:"
        return groups_text
    
    @staticmethod
    async def choose_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle group selection."""
        text = update.message.text.strip()
        
        try:
            group_index = int(text) - 1
            admin_groups = context.user_data.get('admin_groups', [])
            
            if 0 <= group_index < len(admin_groups):
                selected_group_id, selected_group_name = admin_groups[group_index]
                context.user_data['selected_group_id'] = selected_group_id
                context.user_data['selected_group_name'] = selected_group_name
                
                # Check if group already has a reward
                current_config = reward_system.get_reward_config(selected_group_id)
                message = RewardHandlers._format_group_selection_message(current_config, selected_group_name)
                
                await update.message.reply_text(message)
                return CHOOSING_TYPE
            else:
                await update.message.reply_text("❌ Invalid group number. Please try again.")
                return CHOOSING_GROUP
        except ValueError:
            await update.message.reply_text("❌ Please reply with a number.")
            return CHOOSING_GROUP
    
    @staticmethod
    def _format_group_selection_message(current_config: Dict[str, Any], selected_group_name: str) -> str:
        """Format the group selection confirmation message."""
        if current_config:
            config_type = current_config.get('type', '')
            total_amount = current_config.get('total_amount', 0)
            
            return (
                f"⚠️ {selected_group_name} already has a {config_type} reward of {total_amount}.\n\n"
                f"Setting a new reward will replace the current one.\n\n"
                f"Choose reward type:\n"
                f"• Reply `pool` for equal distribution\n"
                f"• Reply `rank` for rank-based distribution"
            )
        else:
            return (
                f"✅ Selected: {selected_group_name}\n\n"
                f"Choose reward type:\n"
                f"• Reply `pool` for equal distribution\n"
                f"• Reply `rank` for rank-based distribution"
            )
    
    @staticmethod
    async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle reward type selection."""
        text = update.message.text.strip().lower()
        selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
        
        if text == 'pool':
            context.user_data['reward_type'] = REWARD_TYPE_POOL
            await update.message.reply_text(
                f"🏆 Pool Reward for {selected_group_name}\n\n"
                f"Enter the total reward amount (e.g., 1000):"
            )
            return ENTERING_POOL_AMOUNT
        elif text == 'rank':
            context.user_data['reward_type'] = REWARD_TYPE_RANK
            await update.message.reply_text(
                f"🏆 Rank Reward for {selected_group_name}\n\n"
                f"Enter the total reward amount (e.g., 1000):"
            )
            return ENTERING_RANK_AMOUNT
        else:
            await update.message.reply_text("❌ Please reply with `pool` or `rank`.")
            return CHOOSING_TYPE
    
    @staticmethod
    async def enter_pool_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle pool reward amount input."""
        text = update.message.text.strip()
        selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
        
        try:
            total_amount = float(text)
            if total_amount <= 0:
                await update.message.reply_text("❌ Amount must be positive. Please try again:")
                return ENTERING_POOL_AMOUNT
            
            context.user_data['reward_config'] = {
                'type': REWARD_TYPE_POOL,
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
    
    @staticmethod
    async def enter_rank_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle rank reward amount input."""
        text = update.message.text.strip()
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
    
    @staticmethod
    async def enter_rank_distribution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle rank distribution input."""
        text = update.message.text.strip().lower()
        selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
        total_amount = context.user_data.get('total_amount', 0)
        
        if text == 'default':
            rank_rewards = reward_system.create_default_rank_distribution(total_amount)
            
            context.user_data['reward_config'] = {
                'type': REWARD_TYPE_RANK,
                'total_amount': total_amount,
                'rank_rewards': rank_rewards,
                'group_name': selected_group_name
            }
            
            rank_text = "\n".join([f"• Rank {rank}: {amount:.2f}" for rank, amount in rank_rewards.items()])
            
            await update.message.reply_text(
                f"🏆 Rank Reward for {selected_group_name}\n\n"
                f"Total Amount: {total_amount}\n"
                f"Default Distribution:\n{rank_text}\n\n"
                f"Enter the start time (YYYY-MM-DD HH:MM):\n"
                f"Example: 2024-01-15 14:30"
            )
            
            return ENTERING_START_TIME
        
        elif text.startswith('custom'):
            return await RewardHandlers._handle_custom_distribution(
                update, context, text, total_amount, selected_group_name
            )
        
        else:
            await update.message.reply_text(
                "❌ Please reply with:\n"
                f"• `default` for default distribution\n"
                f"• `custom 600 300 100` for custom amounts"
            )
            return ENTERING_RANK_DISTRIBUTION
    
    @staticmethod
    async def _handle_custom_distribution(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                        text: str, total_amount: float, selected_group_name: str) -> int:
        """Handle custom rank distribution input."""
        parts = text.split()
        if len(parts) > 1:
            try:
                custom_amounts = [float(amount) for amount in parts[1:]]
                
                if not reward_system.validate_custom_rank_distribution(custom_amounts, total_amount):
                    await update.message.reply_text(
                        f"❌ Rank amounts ({sum(custom_amounts)}) must equal total amount ({total_amount}).\n"
                        f"Please try again:"
                    )
                    return ENTERING_RANK_DISTRIBUTION
                
                rank_rewards = {i+1: amount for i, amount in enumerate(custom_amounts)}
                
                context.user_data['reward_config'] = {
                    'type': REWARD_TYPE_RANK,
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
    
    @staticmethod
    async def enter_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle start time input."""
        text = update.message.text.strip()
        selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
        
        try:
            start_time = datetime.strptime(text, DATE_FORMAT)
            context.user_data['start_time'] = start_time
            
            await update.message.reply_text(
                f"🏆 Event Start Time Set\n\n"
                f"Group: {selected_group_name}\n"
                f"Start Time: {start_time.strftime(DATE_FORMAT)}\n\n"
                f"Enter the end time (YYYY-MM-DD HH:MM):\n"
                f"Example: 2024-01-15 18:30"
            )
            
            return ENTERING_END_TIME
            
        except ValueError:
            await update.message.reply_text("❌ Invalid date format. Please use YYYY-MM-DD HH:MM format:\nExample: 2024-01-15 14:30")
            return ENTERING_START_TIME
    
    @staticmethod
    async def enter_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle end time input and complete reward setup."""
        text = update.message.text.strip()
        selected_group_id = context.user_data.get('selected_group_id')
        selected_group_name = context.user_data.get('selected_group_name', 'Unknown Group')
        start_time = context.user_data.get('start_time')
        reward_config = context.user_data.get('reward_config', {})
        
        try:
            end_time = datetime.strptime(text, DATE_FORMAT)
            
            if end_time <= start_time:
                await update.message.reply_text("❌ End time must be after start time. Please try again:")
                return ENTERING_END_TIME
            
            # Complete the reward configuration
            final_config = {
                **reward_config,
                'start_time': start_time,
                'end_time': end_time,
                'status': 'active'
            }
            
            reward_system.set_reward_config(selected_group_id, final_config)
            
            # Send confirmation and announcement
            await RewardHandlers._send_event_confirmation(update, context, final_config, selected_group_id, selected_group_name)
            
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ Invalid date format. Please use YYYY-MM-DD HH:MM format:\nExample: 2024-01-15 18:30")
            return ENTERING_END_TIME
    
    @staticmethod
    async def _send_event_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     config: Dict[str, Any], group_id: int, group_name: str) -> None:
        """Send event confirmation and announcement."""
        # Send confirmation to user
        confirmation = RewardHandlers._format_confirmation_message(config, group_name)
        await update.message.reply_text(confirmation)
        
        # Send announcement to group
        try:
            announcement = reward_system.format_event_announcement(config)
            sent_announcement = await context.bot.send_message(chat_id=group_id, text=announcement)
            
            # Try to pin the announcement
            try:
                await context.bot.pin_chat_message(
                    chat_id=group_id,
                    message_id=sent_announcement.message_id,
                    disable_notification=False
                )
                print(f"📌 Event announcement pinned in {group_name} (ID: {group_id})")
            except Exception as e:
                print(f"Could not pin announcement in group {group_id}: {e}")
            
            print(f"📢 Event announcement sent to {group_name} (ID: {group_id})")
            
        except Exception as e:
            print(f"Could not send event announcement to group {group_id}: {e}")
        
        # Log the action
        logger.info(f"Admin set {config['type']} reward event for group {group_name} (ID: {group_id}): {config['total_amount']}")
        print(f"🏆 {config['type'].title()} reward event set for group {group_name}: {config['total_amount']}")
    
    @staticmethod
    def _format_confirmation_message(config: Dict[str, Any], group_name: str) -> str:
        """Format the confirmation message."""
        start_time = config['start_time']
        end_time = config['end_time']
        
        if config['type'] == REWARD_TYPE_POOL:
            return (
                f"✅ Pool Reward Event Set Successfully!\n\n"
                f"Group: {group_name}\n"
                f"Type: Pool\n"
                f"Total Amount: {config['total_amount']}\n"
                f"Start Time: {start_time.strftime(DATE_FORMAT)}\n"
                f"End Time: {end_time.strftime(DATE_FORMAT)}\n\n"
                f"Rewards will be distributed equally among all participants."
            )
        else:  # rank type
            rank_rewards = config.get('rank_rewards', {})
            rank_text = "\n".join([f"• Rank {rank}: {amount:.2f}" for rank, amount in rank_rewards.items()])
            return (
                f"✅ Rank Reward Event Set Successfully!\n\n"
                f"Group: {group_name}\n"
                f"Type: Rank\n"
                f"Total Amount: {config['total_amount']}\n"
                f"Start Time: {start_time.strftime(DATE_FORMAT)}\n"
                f"End Time: {end_time.strftime(DATE_FORMAT)}\n\n"
                f"Rank Distribution:\n{rank_text}"
            )
    
    @staticmethod
    async def cancel_reward_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the reward setup process."""
        await update.message.reply_text("❌ Reward setup cancelled.")
        return ConversationHandler.END


# Create handler instance
reward_handlers = RewardHandlers()