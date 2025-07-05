"""
Data storage module for user points and group tracking.
"""

from typing import Dict, Any, Optional, List, Tuple
from config.config import *


class DataStorage:
    """Handles storage and retrieval of user data and group information."""
    
    def __init__(self):
        # Dictionary to track user points by group
        # Format: {user_id: {group_id: {'points': float, 'group_name': str}}}
        self.user_points: Dict[int, Dict[int, Dict[str, Any]]] = {}
        
        # Set to track which groups are being listened to
        self.listening_groups: set = set()
    
    def add_listening_group(self, group_id: int) -> None:
        """Add a group to the listening list."""
        self.listening_groups.add(group_id)
    
    def remove_listening_group(self, group_id: int) -> None:
        """Remove a group from the listening list."""
        self.listening_groups.discard(group_id)
    
    def is_listening_to_group(self, group_id: int) -> bool:
        """Check if bot is listening to a specific group."""
        return group_id in self.listening_groups
    
    def get_listening_groups(self) -> set:
        """Get all groups being listened to."""
        return self.listening_groups.copy()
    
    def add_user_points(self, user_id: int, group_id: int, points: float, group_name: str) -> None:
        """Add points to a user in a specific group."""
        if user_id not in self.user_points:
            self.user_points[user_id] = {}
        
        if group_id not in self.user_points[user_id]:
            self.user_points[user_id][group_id] = {
                'points': 0,
                'group_name': group_name
            }
        
        self.user_points[user_id][group_id]['points'] += points
        self.user_points[user_id][group_id]['group_name'] = group_name
    
    def get_user_points(self, user_id: int) -> Dict[int, Dict[str, Any]]:
        """Get all points for a user across all groups."""
        return self.user_points.get(user_id, {})
    
    def get_user_points_in_group(self, user_id: int, group_id: int) -> float:
        """Get points for a user in a specific group."""
        user_data = self.user_points.get(user_id, {})
        group_data = user_data.get(group_id, {})
        return group_data.get('points', 0)
    
    def get_user_points_by_group_name(self, user_id: int, group_name: str) -> List[Tuple[int, Dict[str, Any]]]:
        """Get user points for groups matching a specific name."""
        user_data = self.user_points.get(user_id, {})
        matching_groups = []
        
        for group_id, group_data in user_data.items():
            if isinstance(group_data, dict) and group_data.get('group_name', '').lower() == group_name.lower():
                matching_groups.append((group_id, group_data))
        
        return matching_groups
    
    def get_total_user_points(self, user_id: int) -> float:
        """Get total points for a user across all groups."""
        user_data = self.user_points.get(user_id, {})
        total = 0
        
        for group_data in user_data.values():
            if isinstance(group_data, dict):
                total += group_data.get('points', 0)
        
        return total
    
    def format_user_status(self, user_id: int, group_name: Optional[str] = None) -> str:
        """Format user status message."""
        if group_name:
            matching_groups = self.get_user_points_by_group_name(user_id, group_name)
            if matching_groups:
                status_text = f"📊 Your Points in '{group_name}'\n\n"
                for group_id, group_data in matching_groups:
                    points = group_data.get('points', 0)
                    status_text += f"• {group_data.get('group_name', 'Unknown Group')}: {points:.2f} points\n"
                return status_text
            else:
                return f"❌ No points found for group '{group_name}'"
        else:
            # Show all groups
            user_group_points = self.get_user_points(user_id)
            
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
                return status_text
            else:
                return "❌ No points found. Start chatting in groups where the bot is listening!"
    
    def get_listening_groups_count(self) -> int:
        """Get count of groups being listened to."""
        return len(self.listening_groups)
    
    def get_total_users_count(self) -> int:
        """Get count of users with points."""
        return len(self.user_points)


# Global data storage instance
data_storage = DataStorage()