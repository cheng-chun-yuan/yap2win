"""
User verification module for bot access control.
"""

from typing import Dict, Set, Optional, Any
from config.config import VERIFICATION_MESSAGE, VERIFICATION_RESPONSE
from services.nft_service import nft_service


class VerificationRule:
    """Represents a verification rule for a group."""
    
    def __init__(self, country: Optional[str] = None, age: Optional[int] = None, 
                 nft_holder: Optional[str] = None, collect_address: bool = True):
        self.country = country
        self.age = age
        self.nft_holder = nft_holder
        self.collect_address = collect_address
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            'country': self.country,
            'age': self.age,
            'nft_holder': self.nft_holder,
            'collect_address': self.collect_address
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VerificationRule':
        """Create rule from dictionary."""
        return cls(
            country=data.get('country'),
            age=data.get('age'),
            nft_holder=data.get('nft_holder'),
            collect_address=data.get('collect_address', True)
        )


class UserVerification:
    """Handles user verification logic."""
    
    def __init__(self):
        self.verified_users: Set[int] = set()
        self.group_rules: Dict[int, VerificationRule] = {}
        self.pending_verifications: Dict[int, Dict[str, Any]] = {}
        self.user_addresses: Dict[int, str] = {}
    
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
    
    def set_group_rule(self, group_id: int, rule: VerificationRule) -> None:
        """Set verification rule for a group."""
        self.group_rules[group_id] = rule
    
    def get_group_rule(self, group_id: int) -> Optional[VerificationRule]:
        """Get verification rule for a group."""
        return self.group_rules.get(group_id)
    
    def has_group_rule(self, group_id: int) -> bool:
        """Check if group has verification rule."""
        return group_id in self.group_rules
    
    def check_verification_requirements(self, user_id: int, group_id: int, 
                                      user_data: Dict[str, Any]) -> bool:
        """Check if user meets verification requirements for group."""
        rule = self.get_group_rule(group_id)
        if not rule:
            return True  # No rule set, allow all
        
        # Check country requirement
        if rule.country and rule.country != "None":
            if user_data.get('country', '').lower() != rule.country.lower():
                return False
        
        # Check age requirement
        if rule.age and rule.age > 0:
            user_age = user_data.get('age', 0)
            if user_age < rule.age:
                return False
        
        # Check NFT holder requirement
        if rule.nft_holder is not None:
            wallet_address = user_data.get('address') or self.get_user_address(user_id)
            if wallet_address:
                # Check actual NFT balance using blockchain
                nft_verified = nft_service.verify_nft_requirement(wallet_address, rule.nft_holder)
                if not nft_verified:
                    return False
            else:
                # No wallet address provided, fail NFT verification
                return False
        
        return True
    
    def get_verification_requirements_text(self, group_id: int) -> str:
        """Get text description of verification requirements for group."""
        rule = self.get_group_rule(group_id)
        if not rule:
            return "No verification requirements set."
        
        requirements = []
        
        if rule.country and rule.country != "None":
            requirements.append(f"Country: {rule.country}")
        
        if rule.age and rule.age > 0:
            requirements.append(f"Minimum age: {rule.age}")
        
        if rule.nft_holder is not None:
            if isinstance(rule.nft_holder, str):
                requirements.append(f"NFT holder: {rule.nft_holder.title()}")
            else:
                requirements.append(f"NFT holder: {'Yes' if rule.nft_holder else 'No'}")
        
        if rule.collect_address:
            requirements.append("Wallet address for rewards")
        
        if not requirements:
            return "No verification requirements set."
        
        return "Requirements:\n" + "\n".join(f"• {req}" for req in requirements)
    
    def start_verification_process(self, user_id: int, group_id: int) -> None:
        """Start verification process for user."""
        self.pending_verifications[user_id] = {
            'group_id': group_id,
            'step': 'country',
            'data': {}
        }
    
    def get_pending_verification(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get pending verification for user."""
        return self.pending_verifications.get(user_id)
    
    def update_verification_data(self, user_id: int, key: str, value: Any) -> None:
        """Update verification data for user."""
        if user_id in self.pending_verifications:
            self.pending_verifications[user_id]['data'][key] = value
    
    def advance_verification_step(self, user_id: int, next_step: str) -> None:
        """Advance verification to next step."""
        if user_id in self.pending_verifications:
            self.pending_verifications[user_id]['step'] = next_step
    
    def complete_verification(self, user_id: int) -> bool:
        """Complete verification process and check if user passes."""
        if user_id not in self.pending_verifications:
            return False
        
        verification = self.pending_verifications[user_id]
        group_id = verification['group_id']
        user_data = verification['data']
        
        # Check if user meets requirements
        passed = self.check_verification_requirements(user_id, group_id, user_data)
        
        if passed:
            self.verified_users.add(user_id)
            # Store wallet address if provided
            if 'address' in user_data:
                self.user_addresses[user_id] = user_data['address']
        
        # Clean up pending verification
        del self.pending_verifications[user_id]
        
        return passed
    
    def get_user_address(self, user_id: int) -> Optional[str]:
        """Get user's wallet address."""
        return self.user_addresses.get(user_id)
    
    def set_user_address(self, user_id: int, address: str) -> None:
        """Set user's wallet address."""
        self.user_addresses[user_id] = address
    
    def verify_user_nft(self, user_id: int, nft_type: str) -> bool:
        """
        Verify if user holds required NFTs.
        
        Args:
            user_id: User's ID
            nft_type: Required NFT type ('penguin' or 'ape')
            
        Returns:
            True if user holds required NFTs, False otherwise
        """
        wallet_address = self.get_user_address(user_id)
        if not wallet_address:
            return False
        
        return nft_service.verify_nft_requirement(wallet_address, nft_type)
    
    def get_user_nft_summary(self, user_id: int) -> Optional[Dict[str, int]]:
        """
        Get summary of user's NFT holdings.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dictionary with NFT types and balances, or None if no wallet address
        """
        wallet_address = self.get_user_address(user_id)
        if not wallet_address:
            return None
        
        return nft_service.get_nft_summary(wallet_address)


# Global verification instance
verification = UserVerification()