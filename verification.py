"""
User verification module for bot access control.
"""

from typing import Dict, Set
from config import VERIFICATION_MESSAGE, VERIFICATION_RESPONSE


class UserVerification:
    """Handles user verification logic."""
    
    def __init__(self):
        self.verified_users: Set[int] = set()
    
    def is_verification_message(self, text: str) -> bool:
        """Check if the message is a verification message."""
        return text.lower().strip() == VERIFICATION_MESSAGE
    
    def verify_user(self, user_id: int) -> str:
        """Verify a user and return response message."""
        self.verified_users.add(user_id)
        return VERIFICATION_RESPONSE
    
    def is_user_verified(self, user_id: int) -> bool:
        """Check if a user is verified."""
        # For now, return True to allow all users
        # In production, this would check against a database or service
        return True
        # return user_id in self.verified_users
    
    def get_unverified_user_message(self) -> str:
        """Get message to send to unverified users."""
        return 'You must verify with the bot in private chat by saying "I am human" before participating in the group.'
    
    def get_verification_count(self) -> int:
        """Get the number of verified users."""
        return len(self.verified_users)


# Global verification instance
verification = UserVerification()