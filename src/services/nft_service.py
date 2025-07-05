"""
NFT balance checking service for Ethereum mainnet.
"""

import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class NFTService:
    """Service for checking NFT balances on Ethereum mainnet."""
    
    # Known NFT contract addresses (examples)
    CONTRACT_ADDRESSES = {
        'penguin': '0xBd3531dA5CF5857e7CfAA92426877b022e612cf8',  # Pudgy Penguins
        'ape': '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D',     # Bored Ape Yacht Club
    }
    
    # ERC-721 ABI for balanceOf function
    ERC721_ABI = [
        {
            "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "name",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "symbol",
            "outputs": [{"internalType": "string", "name": "", "type": "string"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    def __init__(self):
        """Initialize NFT service with Web3 connection."""
        try:
            from web3 import Web3
            
            # Use public Ethereum RPC endpoints
            rpc_endpoints = [
                'https://eth.public-rpc.com',
                'https://ethereum.publicnode.com',
                'https://rpc.ankr.com/eth',
                'https://eth-mainnet.public.blastapi.io'
            ]
            
            self.w3 = None
            for endpoint in rpc_endpoints:
                try:
                    w3 = Web3(Web3.HTTPProvider(endpoint))
                    if w3.is_connected():
                        self.w3 = w3
                        logger.info(f"Connected to Ethereum mainnet via {endpoint}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to connect to {endpoint}: {e}")
                    continue
            
            if not self.w3:
                logger.error("Failed to connect to any Ethereum RPC endpoint")
                raise ConnectionError("Cannot connect to Ethereum mainnet")
                
        except ImportError:
            logger.error("web3 package not installed. Install with: pip install web3")
            raise ImportError("web3 package required for NFT verification")
    
    def check_nft_balance(self, wallet_address: str, nft_type: str) -> int:
        """
        Check NFT balance for a wallet address.
        
        Args:
            wallet_address: Ethereum wallet address
            nft_type: Type of NFT ('penguin' or 'ape')
            
        Returns:
            Number of NFTs owned
        """
        # Validate address format
        if not self._is_valid_address(wallet_address):
            logger.error(f"Invalid Ethereum address format: {wallet_address}")
            return 0
            
        return self._check_balance_onchain(wallet_address, nft_type)
    
    def _is_valid_address(self, address: str) -> bool:
        """Validate Ethereum address format."""
        try:
            # Basic format check
            if not address or not isinstance(address, str):
                return False
            
            # Check if it starts with 0x and has correct length
            if not address.startswith('0x') or len(address) != 42:
                return False
            
            # Try to convert to checksum address (this validates the address)
            self.w3.to_checksum_address(address)
            return True
            
        except Exception:
            return False
    
    def _check_balance_onchain(self, wallet_address: str, nft_type: str) -> int:
        """Check NFT balance directly from blockchain."""
        try:
            contract_address = self.CONTRACT_ADDRESSES.get(nft_type)
            if not contract_address:
                logger.error(f"Unknown NFT type: {nft_type}")
                return 0
            
            # Convert addresses to checksum format
            checksum_wallet = self.w3.to_checksum_address(wallet_address)
            checksum_contract = self.w3.to_checksum_address(contract_address)
            
            logger.info(f"Checking {nft_type} balance for {checksum_wallet} on-chain...")
            
            # Create contract instance
            contract = self.w3.eth.contract(
                address=checksum_contract,
                abi=self.ERC721_ABI
            )
            
            # Call balanceOf function
            balance = contract.functions.balanceOf(checksum_wallet).call()
            
            logger.info(f"On-chain: Found {balance} {nft_type} NFTs for {checksum_wallet}")
            return balance
            
        except Exception as e:
            logger.error(f"Error checking NFT balance on-chain: {e}")
            return 0
    
    def verify_nft_requirement(self, wallet_address: str, required_nft: str) -> bool:
        """
        Verify if wallet meets NFT requirement.
        
        Args:
            wallet_address: Ethereum wallet address
            required_nft: Required NFT type ('penguin' or 'ape')
            
        Returns:
            True if requirement is met, False otherwise
        """
        if not wallet_address or not required_nft:
            logger.warning(f"Invalid parameters: wallet_address={wallet_address}, required_nft={required_nft}")
            return False
        
        # Validate address format
        if not self._is_valid_address(wallet_address):
            logger.error(f"Invalid wallet address format: {wallet_address}")
            return False
        
        balance = self.check_nft_balance(wallet_address, required_nft)
        meets_requirement = balance > 0
        
        # Convert to checksum for logging
        checksum_address = self.w3.to_checksum_address(wallet_address)
        logger.info(f"NFT verification: {checksum_address} has {balance} {required_nft} NFTs - {'PASS' if meets_requirement else 'FAIL'}")
        return meets_requirement
    
    def get_nft_summary(self, wallet_address: str) -> Dict[str, int]:
        """
        Get summary of all NFTs for a wallet.
        
        Args:
            wallet_address: Ethereum wallet address
            
        Returns:
            Dictionary with NFT types and balances
        """
        summary = {}
        for nft_type in self.CONTRACT_ADDRESSES.keys():
            balance = self.check_nft_balance(wallet_address, nft_type)
            summary[nft_type] = balance
        
        return summary
    
    def get_supported_nfts(self) -> list:
        """Get list of supported NFT types."""
        return list(self.CONTRACT_ADDRESSES.keys())
    
    def get_contract_info(self, nft_type: str) -> Optional[Dict[str, Any]]:
        """
        Get contract information for NFT type.
        
        Args:
            nft_type: Type of NFT
            
        Returns:
            Dictionary with contract address and other info
        """
        contract_address = self.CONTRACT_ADDRESSES.get(nft_type)
        if not contract_address:
            return None
        
        try:
            # Convert to checksum address
            checksum_address = self.w3.to_checksum_address(contract_address)
            
            contract = self.w3.eth.contract(
                address=checksum_address,
                abi=self.ERC721_ABI
            )
            
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            
            return {
                'address': checksum_address,
                'name': name,
                'symbol': symbol,
                'type': nft_type
            }
        except Exception as e:
            logger.error(f"Error getting contract info for {nft_type}: {e}")
            return {
                'address': contract_address,
                'name': f'{nft_type.title()} NFT',
                'symbol': nft_type.upper(),
                'type': nft_type
            }


# Global NFT service instance (direct on-chain access)
nft_service = NFTService()