"""
ROFL Wallet Service for secure wallet generation and management.

This service provides integration with the ROFL (Remote Oracle Function Layer) appd REST API
as documented at https://docs.oasis.io/build/rofl/features/rest.

The service communicates with rofl-appd via Unix domain socket at /run/rofl-appd.sock
and provides methods for:
- Key generation (secp256k1 keys)
- App identifier retrieval
- Authenticated transaction submission

All operations are performed through the attested ROFL environment for maximum security.
"""

import httpx
import json
import logging
from typing import Dict, Any
from eth_account import Account
from web3 import Web3
import time

logger = logging.getLogger(__name__)


class ROFLWalletService:
    """Service for ROFL wallet operations."""
    
    def __init__(self, rofl_socket_path: str = "/run/rofl-appd.sock"):
        self.socket_path = rofl_socket_path
        self.web3 = Web3()
    
    def _appd_post(self, path: str, payload: Any) -> Any:
        """
        Make a POST request to ROFL appd via Unix domain socket.
        
        According to https://docs.oasis.io/build/rofl/features/rest, the API is exposed
        via a UNIX socket at /run/rofl-appd.sock and uses HTTP protocol over the socket.
        """
        try:
            transport = httpx.HTTPTransport(uds=self.socket_path)
            logger.info(f"Using unix domain socket: {self.socket_path}")
            
            with httpx.Client(transport=transport) as client:
                url = "http://localhost"
                logger.info(f"Posting {json.dumps(payload)} to {url + path}")
                response = client.post(url + path, json=payload, timeout=30.0)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in _appd_post: {e}")
            raise
    
    def generate_wallet(self, pool_id: str) -> Dict:
        """
        Generate a new wallet for a reward pool.
        
        Uses the ROFL key generation endpoint: /rofl/v1/keys/generate (POST)
        as documented at https://docs.oasis.io/build/rofl/features/rest#key-generation
        
        The generated keys are domain-separated by key_id and remain consistent
        across deployments due to the attested ROFL environment.
        """
        try:
            payload = {
                "key_id": f"reward_pool_{pool_id}",
                "kind": "secp256k1"
            }
            
            path = '/rofl/v1/keys/generate'
            response = self._appd_post(path, payload)
            
            private_key = response["key"]
            wallet_address = self._derive_address(private_key)
            
            return {
                "pool_id": pool_id,
                "private_key": private_key,
                "address": wallet_address,
                "app_id": self.get_app_id(),
                "created_at": int(time.time())
            }
                
        except Exception as e:
            logger.error(f"Unexpected error generating wallet: {e}")
            raise
    
    def get_app_id(self) -> str:
        """
        Get the ROFL app identifier.
        
        Uses the ROFL app identifier endpoint: /rofl/v1/app/id (GET)
        as documented at https://docs.oasis.io/build/rofl/features/rest#app-identifier
        
        Returns the unique identifier for the current ROFL app instance.
        """
        try:
            transport = httpx.HTTPTransport(uds=self.socket_path)
            logger.info(f"Getting app ID via unix domain socket: {self.socket_path}")
            
            with httpx.Client(transport=transport) as client:
                url = "http://localhost"
                path = '/rofl/v1/app/id'
                logger.info(f"Getting app ID from {url + path}")
                response = client.get(url + path, timeout=10.0)
                response.raise_for_status()
                return response.text.strip()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting app ID: {e.response.status_code} - {e.response.text}")
            return "unknown"
        except httpx.RequestError as e:
            logger.error(f"Request error getting app ID: {e}")
            return "unknown"
        except Exception as e:
            logger.error(f"Unexpected error getting app ID: {e}")
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
        """
        Submit authenticated transaction via ROFL.
        
        Uses the ROFL authenticated transaction submission endpoint: /rofl/v1/tx/sign-submit (POST)
        as documented at https://docs.oasis.io/build/rofl/features/rest#authenticated-transaction-submission
        
        These transactions are signed by an endorsed key and automatically authenticated
        as coming from the ROFL app itself, making them suitable for smart contract
        authentication via Subcall.roflEnsureAuthorizedOrigin(roflAppID).
        """
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
            
            path = '/rofl/v1/tx/sign-submit'
            return self._appd_post(path, payload)
                
        except Exception as e:
            logger.error(f"Unexpected error submitting transaction: {e}")
            raise


# Global instance
rofl_service = ROFLWalletService()