"""
Message processing module for the Telegram bot.
"""

import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from config.config import GROUP_CHAT_TYPES, PRIVATE_CHAT_TYPE
from services.data_storage import data_storage
from services.reward_system import reward_system
from services.deepeval_scoring import deepeval_scorer
from utils.verification import verification
from handlers.handlers import VerificationHandlers

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Handles message processing and scoring."""
    
    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
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
        user_id = user.id if user else None
        chat_id = chat.id if chat else None
        message_id = message.message_id if message else None
        text = message.text if message else None
        
        if not MessageProcessor._validate_message_data(user_id, chat_id, message_id, text):
            return
        
        # Log message processing
        text_preview = text[:50] + '...' if len(text) > 50 else text
        print(f'Processing message from user {user_id} in chat {chat_id}: "{text_preview}"')
        
        # Handle verification in private chat
        if chat.type == PRIVATE_CHAT_TYPE:
            # Check for verification conversations
            if context.user_data.get('setting_rule_for_group'):
                await VerificationHandlers.handle_rule_setting(update, context)
                return
            elif context.user_data.get('selecting_group_for_rule_setting'):
                await VerificationHandlers.handle_admin_group_selection(update, context)
                return
            elif context.user_data.get('selecting_group_for_verification'):
                await VerificationHandlers.handle_group_selection(update, context)
                return
            elif context.user_data.get('verifying_for_group'):
                await VerificationHandlers.handle_verification(update, context)
                return
            elif context.user_data.get('awaiting_group_selection_for_verification'):
                await VerificationHandlers.handle_group_selection_for_verification(update, context)
                return
            elif context.user_data.get('collecting_verification_data_for_group'):
                await VerificationHandlers.handle_verification_data_collection(update, context)
                return
            elif verification.is_verification_message(text):
                response = verification.verify_user(user_id)
                await message.reply_text(response)
                print(f'User {user_id} verified in private chat')
                return
        
        # Handle group messages
        if chat.type in GROUP_CHAT_TYPES:
            await MessageProcessor._handle_group_message(update, context, user, chat, text)
    
    @staticmethod
    def _validate_message_data(user_id: int, chat_id: int, message_id: int, text: str) -> bool:
        """Validate message data completeness."""
        if not user_id or not chat_id or not message_id or not text:
            print('Missing required message data:', {
                'userId': user_id, 
                'chatId': chat_id, 
                'messageId': message_id, 
                'hasText': bool(text)
            })
            return False
        return True
    
    @staticmethod
    async def _handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   user: Any, chat: Any, text: str) -> None:
        """Handle messages in group chats."""
        user_id = user.id
        chat_id = chat.id
        
        # Check if user is verified
        if not verification.is_user_verified(user_id):
            await MessageProcessor._handle_unverified_user(context, user_id, chat_id)
            return
        
        # Always process messages and send notifications, regardless of listening status
        try:
            await MessageProcessor._process_and_score_message(update, context, user, chat, text)
        except Exception as error:
            print(f'Error processing message: {error}')
            logger.error(f'Error processing message: {error}')
    
    @staticmethod
    async def _handle_unverified_user(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> None:
        """Handle unverified user in group."""
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=verification.get_unverified_user_message()
            )
        except Exception as e:
            print(f'Could not send DM to user {user_id}: {e}')
        
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            print(f'Kicked unverified user {user_id} from group {chat_id}')
        except Exception as e:
            print(f'Could not kick user {user_id} from group {chat_id}: {e}')
    
    @staticmethod
    async def _process_and_score_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       user: Any, chat: Any, text: str) -> None:
        """Process and score a message."""
        user_id = user.id
        chat_id = chat.id
        
        # Get user info
        user_info = {
            'username': user.username,
            'firstName': user.first_name,
            'lastName': user.last_name
        }
        
        # Calculate score using DeepEval LLM-as-a-judge
        score = deepeval_scorer.calculate_score(text, user_info, group_name=chat.title or "Community")
        
        print(f'Message processed, score: {score}')
        print(f'User {user_id} earned {score:.2f} points in chat {chat_id}')
        
        # Track points and handle event participation
        if score > 0:
            await MessageProcessor._handle_positive_score(update, context, user, chat, score)
        else:
            print(f"🤖 No response for message with 0 score from {user.first_name}")
        
        # Log user message
        logger.info(f"User {user.first_name} (ID: {user.id}) sent message: {text}")
        print(f"💬 User {user.first_name} (ID: {user.id}) sent: {text}")
        
        # Only check for finished events if the group is being listened to
        if data_storage.is_listening_to_group(chat_id):
            await MessageProcessor._check_finished_events(context)
    
    @staticmethod
    async def _handle_positive_score(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   user: Any, chat: Any, score: float) -> None:
        """Handle positive score - update points and send notification."""
        user_id = user.id
        chat_id = chat.id
        group_name = chat.title if chat.title else 'Unknown Group'
        
        # Update user points (always add to general points)
        data_storage.add_user_points(user_id, chat_id, score, group_name)
        
        current_points = data_storage.get_user_points_in_group(user_id, chat_id)
        print(f"📊 Updated points for user {user_id} in group {group_name}: {current_points:.2f}")
        
        # Only track event participation if the group is being listened to
        if data_storage.is_listening_to_group(chat_id):
            # Check if there's an active event before adding event points
            if reward_system.is_event_active(chat_id):
                reward_system.add_participant_score(chat_id, user_id, score, user.username, user.first_name)
                print(f"🎯 Event participant {user.first_name} earned {score:.2f} points in {group_name}")
            else:
                # Check if there's an event configuration but it's not active
                config = reward_system.get_reward_config(chat_id)
                if config:
                    current_time = datetime.now()
                    start_time = config.get('start_time')
                    end_time = config.get('end_time')
                    
                    if start_time and current_time < start_time:
                        print(f"⏰ Event not started yet for group {group_name} (starts at {start_time})")
                    elif end_time and current_time > end_time:
                        print(f"🏁 Event already finished for group {group_name} (ended at {end_time})")
                    else:
                        print(f"⚠️ Event not active for group {group_name} (status: {config.get('status')})")
                else:
                    print(f"📝 No event configured for group {group_name}")
        else:
            print(f"📝 Group {group_name} not being listened to - points tracked but no event participation")
        
        # Send score notification (always send, regardless of listening status)
        await MessageProcessor._send_score_notification(update, context, user, score, group_name)
    
    @staticmethod
    async def _send_score_notification(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     user: Any, score: float, group_name: str) -> None:
        """Send score notification to user."""
        response = deepeval_scorer.format_score_message(score, group_name)
        
        # Try to send to user's private chat instead of group
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=response,
                parse_mode='Markdown'
            )
            print(f"🎯 Sent {score:.2f} points notification to {user.first_name} in private chat (from {group_name})")
        except Exception as e:
            # If can't send to private chat, fall back to group reply
            print(f"Could not send DM to user {user.id}: {e}")
            await update.message.reply_text(response, parse_mode='Markdown')
            print(f"🎯 User {user.first_name} earned {score:.2f} points! (sent in group)")
        
        # Log bot response
        logger.info(f"Bot responded to {user.first_name}: {response}")
    
    @staticmethod
    async def _check_finished_events(context: ContextTypes.DEFAULT_TYPE) -> None:
        """Check for finished events and send results to groups."""
        finished_events = reward_system.get_finished_events()
        
        for group_id, config in finished_events:
            await MessageProcessor._send_event_results(context, group_id, config)
    
    @staticmethod
    async def _send_event_results(context: ContextTypes.DEFAULT_TYPE, group_id: int, config: Dict[str, Any]) -> None:
        """Send event results to the group."""
        try:
            group_name = config.get('group_name', 'Unknown Group')
            
            # Mark event as finished
            reward_system.finish_event(group_id)
            
            # Get and send results
            result_message = reward_system.get_event_results(group_id)
            
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


# Create processor instance
message_processor = MessageProcessor()