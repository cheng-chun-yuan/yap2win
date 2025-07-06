"""
Smart contract service for handling reward pool transactions.
"""

import logging
from datetime import datetime
from typing import Dict, Any
from web3 import Web3

from config.abi import reward_pool_abi
from config.config import CONTRACT_ADDRESS
from services.rofl_service import rofl_service

logger = logging.getLogger(__name__)


class SmartContractService:
    """Handles smart contract interactions."""
    
    def __init__(self):
        # Use HTTP provider for Oasis Sapphire
        self.w3 = Web3(Web3.HTTPProvider('https://sapphire.oasis.io'))
        self.contract = self.w3.eth.contract(address=CONTRACT_ADDRESS, abi=reward_pool_abi)
    
    async def create_reward_pool(self, group_id: int, group_name: str, 
                               start_time: datetime, end_time: datetime, 
                               total_amount: float) -> Dict[str, Any]:
        """
        Create a reward pool on-chain for a group.
        
        Args:
            group_id: Telegram group ID
            group_name: Group name for display
            start_time: Event start time set by user
            end_time: Event end time set by user
            total_amount: Total reward amount set by user
            
        Returns:
            Transaction result dictionary
        """
        try:
            logger.info(f"Creating reward pool for group {group_id} ({group_name})")
            
            # Prepare pool parameters
            pool_name = f"Group_{group_id}_Pool"
            start_timestamp = int(start_time.timestamp())
            end_timestamp = int(end_time.timestamp())
            
            logger.info(f"Pool parameters - Name: {pool_name}, Start: {start_timestamp}, End: {end_timestamp}")
            
            # Encode function call
            function_data = self.contract.encode_abi(['string', 'uint256', 'uint256'], [pool_name, start_timestamp, end_timestamp])
            
            # Convert amount to wei (use user-specified amount)
            amount_wei = int(total_amount * 10**18)
            
            logger.info(f"Submitting transaction - To: {CONTRACT_ADDRESS}, Value: {amount_wei} wei")
            
            # Submit transaction via ROFL
            tx_result = rofl_service.submit_authenticated_tx(
                to_address=CONTRACT_ADDRESS,
                data=function_data,
                value=amount_wei
            )
            
            logger.info(f"Transaction result: {tx_result}")
            
            return {
                'success': bool(tx_result),
                'pool_name': pool_name,
                'start_time': start_timestamp,
                'end_time': end_timestamp,
                'amount': total_amount,
                'contract_address': CONTRACT_ADDRESS,
                'transaction_hash': tx_result.get('hash') if tx_result else None,
                'status': tx_result.get('status') if tx_result else 'failed'
            }
            
        except Exception as e:
            logger.error(f"Error creating reward pool: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def format_pool_creation_message(self, result: Dict[str, Any], group_name: str) -> str:
        """Format pool creation result message."""
        if result['success']:
            return (
                f"🎉 **Reward Pool Created Successfully!**\n\n"
                f"Group: {group_name}\n"
                f"Pool Name: `{result['pool_name']}`\n"
                f"💰 **Amount Funded**: {result['amount']} ROSE\n"
                f"Contract: `{result['contract_address']}`\n"
                f"Start Time: {datetime.fromtimestamp(result['start_time']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"End Time: {datetime.fromtimestamp(result['end_time']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Transaction Hash: `{result.get('transaction_hash', 'N/A')}`\n"
                f"Status: {'✅ Success' if result.get('status') == 'success' else '⏳ Pending'}\n\n"
                f"The reward pool has been created and funded on-chain via ROFL smart contract."
            )
        else:
            return (
                f"⚠️ **Smart Contract Transaction Failed**\n\n"
                f"The verification rule was saved locally but could not be recorded on-chain.\n"
                f"Error: {result.get('error', 'Unknown error')}\n\n"
                f"The rule is still active and functional."
            )


# Global service instance
smart_contract_service = SmartContractService()