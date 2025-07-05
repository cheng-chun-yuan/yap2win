"""
Reward system module for managing events and distributions.
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from config.config import (
    DEFAULT_RANK_DISTRIBUTION, EVENT_STATUS_ACTIVE, EVENT_STATUS_FINISHED,
    REWARD_TYPE_POOL, REWARD_TYPE_RANK, DATE_FORMAT
)
import logging

logger = logging.getLogger(__name__)


class RewardSystem:
    """Handles reward configurations and event management."""
    
    def __init__(self):
        self.reward_configs: Dict[int, Dict[str, Any]] = {}
        self.event_participants: Dict[int, Dict[int, Dict[str, Any]]] = {}
    
    def set_reward_config(self, group_id: int, config: Dict[str, Any]) -> None:
        """Set reward configuration for a group."""
        self.reward_configs[group_id] = config
        # Initialize event participants
        self.event_participants[group_id] = {}
    
    def get_reward_config(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get reward configuration for a group."""
        return self.reward_configs.get(group_id)
    
    def is_event_active(self, group_id: int) -> bool:
        """Check if an event is active for a group."""
        config = self.reward_configs.get(group_id)
        if not config or config.get('status') != EVENT_STATUS_ACTIVE:
            return False
        
        # Check if current time is within event timeframe
        current_time = datetime.now()
        start_time = config.get('start_time')
        end_time = config.get('end_time')
        
        if not start_time or not end_time:
            return False
        
        return start_time <= current_time <= end_time
    
    def is_event_started(self, group_id: int) -> bool:
        """Check if an event has started (regardless of status)."""
        config = self.reward_configs.get(group_id)
        if not config:
            return False
        
        current_time = datetime.now()
        start_time = config.get('start_time')
        
        return start_time and current_time >= start_time
    
    def is_event_finished(self, group_id: int) -> bool:
        """Check if an event has finished (passed end time)."""
        config = self.reward_configs.get(group_id)
        if not config:
            return False
        
        current_time = datetime.now()
        end_time = config.get('end_time')
        
        return end_time and current_time > end_time
    
    def get_event_status(self, group_id: int) -> str:
        """Get detailed event status."""
        config = self.reward_configs.get(group_id)
        if not config:
            return "no_event"
        
        current_time = datetime.now()
        start_time = config.get('start_time')
        end_time = config.get('end_time')
        status = config.get('status')
        
        if status == EVENT_STATUS_FINISHED:
            return "finished"
        
        if not start_time or not end_time:
            return "invalid_config"
        
        if current_time < start_time:
            return "not_started"
        elif current_time > end_time:
            return "time_expired"
        else:
            return "active"
    
    def add_participant_score(self, group_id: int, user_id: int, score: float, 
                            username: str, first_name: str) -> None:
        """Add score to a participant in an event."""
        # Only add points if event is actually active (within time window)
        if not self.is_event_active(group_id):
            print(f"⚠️ Event not active for group {group_id}, skipping points for user {user_id}")
            return
        
        if group_id not in self.event_participants:
            self.event_participants[group_id] = {}
        
        if user_id not in self.event_participants[group_id]:
            self.event_participants[group_id][user_id] = {
                'points': 0,
                'username': username,
                'first_name': first_name
            }
        
        self.event_participants[group_id][user_id]['points'] += score
        self.event_participants[group_id][user_id]['username'] = username
        self.event_participants[group_id][user_id]['first_name'] = first_name
        print(f"✅ Added {score:.2f} points to user {user_id} in active event for group {group_id}")
    
    def get_event_participants(self, group_id: int) -> Dict[int, Dict[str, Any]]:
        """Get all participants for a specific event."""
        return self.event_participants.get(group_id, {})
    
    def get_active_events(self) -> Dict[int, Dict[str, Any]]:
        """Get all currently active events."""
        active_events = {}
        current_time = datetime.now()
        
        for group_id, config in self.reward_configs.items():
            if (config.get('status') == EVENT_STATUS_ACTIVE and 
                config.get('start_time') and config.get('end_time') and
                config['start_time'] <= current_time <= config['end_time']):
                active_events[group_id] = config
        
        return active_events
    
    def get_finished_events(self) -> List[Tuple[int, Dict[str, Any]]]:
        """Get all events that have finished (passed end time but still marked as active)."""
        current_time = datetime.now()
        finished_events = []
        
        for group_id, config in self.reward_configs.items():
            # Check if event is marked as active but has passed end time
            if (config.get('status') == EVENT_STATUS_ACTIVE and 
                config.get('end_time') and 
                current_time > config['end_time']):
                finished_events.append((group_id, config))
                print(f"🏁 Event for group {group_id} has finished (end time: {config['end_time']})")
        
        return finished_events
    
    def finish_event(self, group_id: int) -> None:
        """Mark an event as finished."""
        if group_id in self.reward_configs:
            config = self.reward_configs[group_id]
            if config.get('status') == EVENT_STATUS_ACTIVE:
                self.reward_configs[group_id]['status'] = EVENT_STATUS_FINISHED
                group_name = config.get('group_name', 'Unknown Group')
                print(f"🏁 Marked event as finished for group {group_name} (ID: {group_id})")
                logger.info(f"Event finished for group {group_name} (ID: {group_id})")
            else:
                print(f"⚠️ Event for group {group_id} is already in status: {config.get('status')}")
        else:
            print(f"❌ No event configuration found for group {group_id}")
    
    def get_event_results(self, group_id: int) -> str:
        """Generate results message for a finished event."""
        config = self.reward_configs.get(group_id)
        if not config:
            return "Event configuration not found."
        
        group_name = config.get('group_name', 'Unknown Group')
        event_type = config.get('type', 'unknown')
        total_amount = config.get('total_amount', 0)
        
        participants = self.event_participants.get(group_id, {})
        
        if not participants:
            return (
                f"🏆 Event Finished - No Participants\n\n"
                f"Event: {group_name}\n"
                f"Type: {event_type.title()}\n"
                f"Total Reward: {total_amount}\n"
                f"Status: No participants joined the event"
            )
        
        # Sort participants by points
        sorted_participants = sorted(
            participants.items(), 
            key=lambda x: x[1]['points'], 
            reverse=True
        )
        
        if event_type == REWARD_TYPE_POOL:
            return self._format_pool_results(
                group_name, total_amount, sorted_participants
            )
        else:  # rank type
            return self._format_rank_results(
                group_name, total_amount, sorted_participants, config
            )
    
    def _format_pool_results(self, group_name: str, total_amount: float, 
                           sorted_participants: List[Tuple[int, Dict[str, Any]]]) -> str:
        """Format pool event results."""
        participant_count = len(sorted_participants)
        share_per_person = total_amount / participant_count if participant_count > 0 else 0
        
        result_message = f"🏆 Pool Event Results - {group_name}\n\n"
        result_message += f"Total Reward: {total_amount}\n"
        result_message += f"Participants: {participant_count}\n"
        result_message += f"Share per person: {share_per_person:.2f}\n\n"
        result_message += "Final Rankings:\n"
        
        for i, (user_id, user_data) in enumerate(sorted_participants, 1):
            display_name = self._get_display_name(user_data)
            points = user_data.get('points', 0)
            result_message += f"{i}. {display_name}: {points:.2f} points\n"
        
        return result_message
    
    def _format_rank_results(self, group_name: str, total_amount: float, 
                           sorted_participants: List[Tuple[int, Dict[str, Any]]],
                           config: Dict[str, Any]) -> str:
        """Format rank event results."""
        rank_rewards = config.get('rank_rewards', {})
        
        result_message = f"🏆 Rank Event Results - {group_name}\n\n"
        result_message += f"Total Reward: {total_amount}\n"
        result_message += f"Participants: {len(sorted_participants)}\n\n"
        result_message += "Final Rankings:\n"
        
        for i, (user_id, user_data) in enumerate(sorted_participants, 1):
            display_name = self._get_display_name(user_data)
            points = user_data.get('points', 0)
            
            # Get reward for this rank
            reward = rank_rewards.get(i, 0)
            reward_text = f" (+{reward:.2f})" if reward > 0 else ""
            
            result_message += f"{i}. {display_name}: {points:.2f} points{reward_text}\n"
        
        return result_message
    
    def _get_display_name(self, user_data: Dict[str, Any]) -> str:
        """Get display name for user."""
        username = user_data.get('username')
        first_name = user_data.get('first_name', 'Unknown')
        return f"@{username}" if username else first_name
    
    def create_default_rank_distribution(self, total_amount: float) -> Dict[int, float]:
        """Create default rank distribution based on total amount."""
        return {
            rank: total_amount * percentage 
            for rank, percentage in DEFAULT_RANK_DISTRIBUTION.items()
        }
    
    def validate_custom_rank_distribution(self, custom_amounts: List[float], 
                                        total_amount: float) -> bool:
        """Validate that custom rank amounts sum to total amount."""
        return abs(sum(custom_amounts) - total_amount) <= 0.01
    
    def format_event_announcement(self, config: Dict[str, Any]) -> str:
        """Format event announcement message."""
        event_type = config.get('type')
        total_amount = config.get('total_amount', 0)
        start_time = config.get('start_time')
        end_time = config.get('end_time')
        
        if event_type == REWARD_TYPE_POOL:
            return (
                f"🎉 NEW POOL EVENT STARTING!\n\n"
                f"Total Reward: {total_amount}\n"
                f"Start Time: {start_time.strftime(DATE_FORMAT)}\n"
                f"End Time: {end_time.strftime(DATE_FORMAT)}\n\n"
                f"Start chatting to earn points! Everyone who participates will get an equal share of the reward pool."
            )
        else:  # rank type
            rank_rewards = config.get('rank_rewards', {})
            rank_text = "\n".join([f"• Rank {rank}: {amount:.2f}" for rank, amount in rank_rewards.items()])
            return (
                f"🏆 NEW RANK EVENT STARTING!\n\n"
                f"Total Reward: {total_amount}\n"
                f"Start Time: {start_time.strftime(DATE_FORMAT)}\n"
                f"End Time: {end_time.strftime(DATE_FORMAT)}\n\n"
                f"Rank Distribution:\n{rank_text}\n\n"
                f"Start chatting to earn points and climb the rankings!"
            )
    
    def get_current_standings(self, group_id: int) -> str:
        """Get current standings for an active event."""
        config = self.reward_configs.get(group_id)
        if not config:
            return "No event configuration found."
        
        if not self.is_event_active(group_id):
            return "No active event in this group."
        
        group_name = config.get('group_name', 'Unknown Group')
        event_type = config.get('type', 'unknown')
        total_amount = config.get('total_amount', 0)
        
        participants = self.event_participants.get(group_id, {})
        
        if not participants:
            return (
                f"📊 **CURRENT STANDINGS**\n\n"
                f"Event: {group_name}\n"
                f"Type: {event_type.title()}\n"
                f"Total Reward: {total_amount}\n\n"
                f"📝 No participants yet. Start chatting to earn points!"
            )
        
        # Sort participants by points
        sorted_participants = sorted(
            participants.items(), 
            key=lambda x: x[1]['points'], 
            reverse=True
        )
        
        # Calculate time remaining
        current_time = datetime.now()
        end_time = config.get('end_time')
        time_remaining = end_time - current_time
        
        hours = int(time_remaining.total_seconds() // 3600)
        minutes = int((time_remaining.total_seconds() % 3600) // 60)
        
        if hours > 24:
            days = hours // 24
            hours = hours % 24
            time_text = f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            time_text = f"{hours}h {minutes}m"
        else:
            time_text = f"{minutes}m"
        
        # Format standings
        standings_text = f"📊 **CURRENT STANDINGS**\n\n"
        standings_text += f"Event: {group_name}\n"
        standings_text += f"Type: {event_type.title()}\n"
        standings_text += f"Total Reward: {total_amount}\n"
        standings_text += f"Participants: {len(participants)}\n"
        standings_text += f"Time Remaining: {time_text}\n\n"
        
        if event_type == REWARD_TYPE_POOL:
            # Calculate total points earned by all participants
            total_points = sum(user_data.get('points', 0) for user_data in participants.values())
            
            print(f"🔍 Pool Distribution Debug:")
            print(f"   Total Reward: {total_amount}")
            print(f"   Total Points: {total_points}")
            print(f"   Participants: {len(participants)}")
            
            if total_points > 0:
                points_per_pool = total_amount / total_points
                print(f"   Each point receives: {points_per_pool:.2f}")
                standings_text += f"💰 **Pool Distribution**\n"
                standings_text += f"Each point will receive: {points_per_pool:.2f}\n\n"
            else:
                print(f"   No points earned yet")
                standings_text += f"💰 **Pool Distribution**\n"
                standings_text += f"Each point will receive: {total_amount:.2f} (no points earned yet)\n\n"
        else:  # rank type
            rank_rewards = config.get('rank_rewards', {})
            standings_text += f"🥇 **Rank Distribution**\n"
            for rank, amount in rank_rewards.items():
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                standings_text += f"{medal} {amount:.2f}\n"
            standings_text += "\n"
        
        standings_text += "🏆 **Current Rankings:**\n"
        
        # Show top 10 participants
        for i, (user_id, user_data) in enumerate(sorted_participants[:10], 1):
            display_name = self._get_display_name(user_data)
            points = user_data.get('points', 0)
            
            # Add medals for top 3
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            standings_text += f"{medal} {display_name}: {points:.2f} points\n"
        
        # If there are more than 10 participants, show user's position if not in top 10
        if len(sorted_participants) > 10:
            standings_text += f"... and {len(sorted_participants) - 10} more participants\n"
        
        return standings_text


# Global reward system instance
reward_system = RewardSystem()