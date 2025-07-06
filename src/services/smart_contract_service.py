"""
Smart contract service for handling reward pool transactions.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from config.config import CONTRACT_ADDRESS
from services.contract_utility import ContractUtility
from services.rofl_service import rofl_service

logger = logging.getLogger(__name__)


class SmartContractService:
    """Handles smart contract interactions."""
    
    def __init__(self, 
                 contract_address: str = CONTRACT_ADDRESS,
                 network_name: str = "sapphire",
                 secret: str = None):
        self.contract_address = contract_address
        self.network_name = network_name
        self.secret = secret
        
        # Initialize contract utility
        if secret:
            self.contract_utility = ContractUtility(network_name, secret)
            # Get reward pool contract ABI and bytecode
            abi, bytecode = ContractUtility.get_contract('RewardPool')
            self.contract = self.contract_utility.w3.eth.contract(address=contract_address, abi=abi)
            self.w3 = self.contract_utility.w3
        else:
            # Fallback to read-only mode for backward compatibility
            from web3 import Web3
            from config.abi import reward_pool_abi
            self.w3 = Web3(Web3.HTTPProvider('https://sapphire.oasis.io'))
            self.contract = self.w3.eth.contract(address=contract_address, abi=reward_pool_abi)
            self.contract_utility = None
    
    def set_oracle_address(self):
        """Set the oracle address in the contract if we have write access."""
        if not self.contract_utility:
            logger.warning("Cannot set oracle address: no contract utility (read-only mode)")
            return
            
        try:
            contract_addr = self.contract.functions.oracle().call()
            if contract_addr != self.w3.eth.default_account:
                logger.info(f"Contract oracle {contract_addr} does not match our address {self.w3.eth.default_account}, updating...")
                tx_params = self.contract.functions.setOracle(self.w3.eth.default_account).build_transaction({
                    'gasPrice': self.w3.eth.gas_price
                })
                tx_hash = rofl_service.submit_tx(tx_params)
                logger.info(f"Got receipt {tx_hash}")
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                logger.info(f"Updated oracle address. Transaction hash: {tx_receipt.transactionHash.hex()}")
            else:
                logger.info(f"Contract oracle {contract_addr} matches our address {self.w3.eth.default_account}")
        except Exception as e:
            logger.error(f"Error setting oracle address: {e}")
    
    async def log_loop(self, poll_interval: int = 2):
        """Listen for contract events and process them."""
        logger.info("Listening for reward pool events...")
        while True:
            try:
                # Listen for pool creation events
                logs = self.contract.events.PoolCreated().get_logs(from_block=self.w3.eth.block_number)
                for log in logs:
                    pool_id = log.args.poolId
                    creator = log.args.creator
                    logger.info(f"New pool created: {pool_id} by {creator}")
                    # Process the event as needed
                    
            except Exception as e:
                logger.error(f"Error in event loop: {e}")
            
            await asyncio.sleep(poll_interval)
    
    def run_event_listener(self) -> None:
        """Run the event listener loop."""
        if not self.contract_utility:
            logger.warning("Cannot run event listener: read-only mode")
            return
            
        self.set_oracle_address()
        
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                asyncio.gather(self.log_loop()))
        finally:
            loop.close()
    
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
            
            # Convert amount to wei (use user-specified amount)
            amount_wei = int(total_amount * 10**18)
            
            logger.info(f"Submitting transaction - To: {self.contract_address}, Value: {amount_wei} wei")
            
            if self.contract_utility:
                # Use direct transaction submission when we have contract utility
                tx_params = self.contract.functions.createPool(
                    pool_name, start_timestamp, end_timestamp
                ).build_transaction({
                    'gasPrice': self.w3.eth.gas_price,
                    'value': amount_wei,
                    'gas': 500000  # Set appropriate gas limit
                })
                
                # Submit transaction via ROFL
                tx_hash = rofl_service.submit_tx(tx_params)
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                tx_result = {
                    'hash': tx_receipt.transactionHash.hex(),
                    'status': 'success' if tx_receipt.status == 1 else 'failed'
                }
            else:
                # Fallback to the existing ROFL authenticated transaction method
                function_data = self.contract.functions.createPool(
                    pool_name, start_timestamp, end_timestamp
                ).build_transaction({
                    'gasPrice': self.w3.eth.gas_price,
                })
                
                tx_result = rofl_service.submit_authenticated_tx(
                    to_address=self.contract_address,
                    data=function_data['data'],
                    value=amount_wei
                )
            
            logger.info(f"Transaction result: {tx_result}")
            
            return {
                'success': bool(tx_result),
                'pool_name': pool_name,
                'start_time': start_timestamp,
                'end_time': end_timestamp,
                'amount': total_amount,
                'contract_address': self.contract_address,
                'transaction_hash': tx_result.get('hash') if tx_result else None,
                'status': tx_result.get('status') if tx_result else 'failed'
            }
            
        except Exception as e:
            logger.error(f"Error creating reward pool: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pool_info(self, pool_id: str) -> Dict[str, Any]:
        """Retrieve pool information from the contract."""
        try:
            pool_info = self.contract.functions.getPool(pool_id).call()
            return {
                'success': True,
                'pool_info': pool_info
            }
        except Exception as e:
            logger.error(f"Error retrieving pool info: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pool_participants(self, pool_id: str) -> Dict[str, Any]:
        """Retrieve pool participants from the contract."""
        try:
            participants = self.contract.functions.getPoolParticipants(pool_id).call()
            return {
                'success': True,
                'participants': participants
            }
        except Exception as e:
            logger.error(f"Error retrieving pool participants: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def submit_pool_result(self, pool_id: str, winners: list, amounts: list) -> Dict[str, Any]:
        """Submit pool results to the contract."""
        try:
            logger.info(f"Submitting results for pool {pool_id}")
            
            if self.contract_utility:
                # Use direct transaction submission
                tx_params = self.contract.functions.submitPoolResults(
                    pool_id, winners, amounts
                ).build_transaction({
                    'gasPrice': self.w3.eth.gas_price,
                    'gas': 300000
                })
                
                tx_hash = rofl_service.submit_tx(tx_params)
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                return {
                    'success': tx_receipt.status == 1,
                    'transaction_hash': tx_receipt.transactionHash.hex(),
                    'status': 'success' if tx_receipt.status == 1 else 'failed'
                }
            else:
                logger.warning("Cannot submit pool results: read-only mode")
                return {
                    'success': False,
                    'error': 'Read-only mode - no contract utility available'
                }
                
        except Exception as e:
            logger.error(f"Error submitting pool results: {e}")
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


# Global service instance (backward compatibility)
smart_contract_service = SmartContractService()
# Factory function for creating service with specific configuration
def create_smart_contract_service(contract_address: str = CONTRACT_ADDRESS,
                                network_name: str = "sapphire",
                                secret: str = None) -> SmartContractService:
    """
    Factory function to create a SmartContractService instance.
    
    Args:
        contract_address: The smart contract address
        network_name: Network to connect to (sapphire, sapphire-testnet, etc.)
        secret: Private key for transaction signing
        
    Returns:
        SmartContractService instance
    """
    return SmartContractService(contract_address, network_name, secret)
