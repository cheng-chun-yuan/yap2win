"""
Reward system module for managing events and distributions.
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from config import (
    DEFAULT_RANK_DISTRIBUTION, EVENT_STATUS_ACTIVE, EVENT_STATUS_FINISHED,
    REWARD_TYPE_POOL, REWARD_TYPE_RANK, DATE_FORMAT
)


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
        return config and config.get('status') == EVENT_STATUS_ACTIVE
    
    def add_participant_score(self, group_id: int, user_id: int, score: float, 
                            username: str, first_name: str) -> None:
        """Add score to a participant in an event."""
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
    
    def get_finished_events(self) -> List[Tuple[int, Dict[str, Any]]]:
        """Get all events that have finished."""
        current_time = datetime.now()
        finished_events = []
        
        for group_id, config in self.reward_configs.items():
            if (config.get('status') == EVENT_STATUS_ACTIVE and 
                config.get('end_time') and 
                current_time >= config['end_time']):
                finished_events.append((group_id, config))
        
        return finished_events
    
    def finish_event(self, group_id: int) -> None:
        """Mark an event as finished."""
        if group_id in self.reward_configs:
            self.reward_configs[group_id]['status'] = EVENT_STATUS_FINISHED
    
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


# Global reward system instance
reward_system = RewardSystem()