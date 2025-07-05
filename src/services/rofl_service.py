"""
ROFL Wallet Service for secure wallet generation and management.
"""

import requests
import logging
from typing import Dict, Optional
from eth_account import Account
from web3 import Web3
import time

logger = logging.getLogger(__name__)


class ROFLWalletService:
    """Service for ROFL wallet operations."""
    
    def __init__(self, rofl_socket_path: str = "/run/rofl-appd.sock"):
        self.base_url = "http://localhost"
        self.socket_path = rofl_socket_path
        self.web3 = Web3()
    
    def generate_wallet(self, pool_id: str) -> Dict:
        """Generate a new wallet for a reward pool."""
        try:
            payload = {
                "key_id": f"reward_pool_{pool_id}",
                "kind": "secp256k1"
            }
            
            response = requests.post(
                f"{self.base_url}/rofl/v1/keys/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                private_key = response.json()["key"]
                wallet_address = self._derive_address(private_key)
                
                return {
                    "pool_id": pool_id,
                    "private_key": private_key,
                    "address": wallet_address,
                    "app_id": self.get_app_id(),
                    "created_at": int(time.time())
                }
            else:
                logger.error(f"Failed to generate wallet: {response.text}")
                raise Exception(f"Failed to generate wallet: {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"Request error generating wallet: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating wallet: {e}")
            raise
    
    def get_app_id(self) -> str:
        """Get the ROFL app identifier."""
        try:
            response = requests.get(f"{self.base_url}/rofl/v1/app/id", timeout=10)
            if response.status_code == 200:
                return response.text.strip()
            else:
                logger.error(f"Failed to get app ID: {response.text}")
                return "unknown"
        except requests.RequestException as e:
            logger.error(f"Request error getting app ID: {e}")
            return "unknown"
    
    def _derive_address(self, private_key: str) -> str:
        """Derive Ethereum-compatible address from private key."""
        try:
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            # Create account from private key
            account = Account.from_key(private_key)
            return account.address
            
        except Exception as e:
            logger.error(f"Error deriving address: {e}")
            raise Exception(f"Failed to derive address: {str(e)}")
    
    def get_wallet_balance(self, address: str, rpc_url: str = "https://sapphire.oasis.io") -> float:
        """Get wallet balance from blockchain."""
        try:
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            if not web3.is_connected():
                raise Exception("Failed to connect to blockchain")
            
            balance_wei = web3.eth.get_balance(address)
            balance_eth = web3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
            
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            raise Exception(f"Failed to get balance: {str(e)}")
    
    def submit_authenticated_tx(self, to_address: str, data: str, value: int = 0) -> Dict:
        """Submit authenticated transaction via ROFL."""
        try:
            payload = {
                "tx": {
                    "kind": "eth",
                    "data": {
                        "gas_limit": 200000,
                        "to": to_address,
                        "value": value,
                        "data": data
                    }
                },
                "encrypt": True
            }
            
            response = requests.post(
                f"{self.base_url}/rofl/v1/tx/sign-submit",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Transaction failed: {response.text}")
                raise Exception(f"Transaction failed: {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"Request error submitting transaction: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error submitting transaction: {e}")
            raise


# Global instance
rofl_service = ROFLWalletService()