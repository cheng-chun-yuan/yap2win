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
import typing
from typing import Dict, Any
from eth_account import Account
from web3 import Web3
from web3.types import TxParams
import time

logger = logging.getLogger(__name__)


class ROFLWalletService:
    """Service for ROFL wallet operations."""
    
    ROFL_SOCKET_PATH = "/run/rofl-appd.sock"
    
    def __init__(self, url: str = ''):
        self.url = url
        self.web3 = Web3()
    
    def _appd_post(self, path: str, payload: typing.Any) -> typing.Any:
        """
        Make a POST request to ROFL appd via Unix domain socket.
        
        According to https://docs.oasis.io/build/rofl/features/rest, the API is exposed
        via a UNIX socket at /run/rofl-appd.sock and uses HTTP protocol over the socket.
        """
        transport = None
        if self.url and not self.url.startswith('http'):
            transport = httpx.HTTPTransport(uds=self.url)
            logger.info(f"Using HTTP socket: {self.url}")
        elif not self.url:
            transport = httpx.HTTPTransport(uds=self.ROFL_SOCKET_PATH)
            logger.info(f"Using unix domain socket: {self.ROFL_SOCKET_PATH}")

        client = httpx.Client(transport=transport)

        url = self.url if self.url and self.url.startswith('http') else "http://localhost"
        logger.info(f"Posting {json.dumps(payload)} to {url+path}")
        response = client.post(url + path, json=payload, timeout=None)
        response.raise_for_status()
        return response.json()
    
    def fetch_key(self, id: str) -> str:
        """
        Fetch a key from ROFL key generation endpoint.
        
        Uses the ROFL key generation endpoint: /rofl/v1/keys/generate (POST)
        as documented at https://docs.oasis.io/build/rofl/features/rest#key-generation
        """
        payload = {
            "key_id": f"reward_pool_{id}",
            "kind": "secp256k1"
        }

        path = '/rofl/v1/keys/generate'
        response = self._appd_post(path, payload)
        return response["key"]
    
    def generate_wallet(self, pool_id: str) -> Dict:
        """
        Generate a new wallet for a reward pool.
        
        Uses the ROFL key generation endpoint: /rofl/v1/keys/generate (POST)
        as documented at https://docs.oasis.io/build/rofl/features/rest#key-generation
        
        The generated keys are domain-separated by key_id and remain consistent
        across deployments due to the attested ROFL environment.
        """
        try:
            private_key = self.fetch_key(f"reward_pool_{pool_id}")
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
            transport = None
            if self.url and not self.url.startswith('http'):
                transport = httpx.HTTPTransport(uds=self.url)
                logger.info(f"Getting app ID via HTTP socket: {self.url}")
            elif not self.url:
                transport = httpx.HTTPTransport(uds=self.ROFL_SOCKET_PATH)
                logger.info(f"Getting app ID via unix domain socket: {self.ROFL_SOCKET_PATH}")

            client = httpx.Client(transport=transport)
            url = self.url if self.url and self.url.startswith('http') else "http://localhost"
            path = '/rofl/v1/app/id'
            logger.info(f"Getting app ID from {url + path}")
            response = client.get(url + path, timeout=10.0)
            response.raise_for_status()
            return response.text.strip()
                
        except Exception as e:
            logger.error(f"Error getting app ID: {e}")
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
    
    def submit_tx(self, tx: TxParams) -> str:
        """
        Submit authenticated transaction via ROFL.
        
        Uses the ROFL authenticated transaction submission endpoint: /rofl/v1/tx/sign-submit (POST)
        as documented at https://docs.oasis.io/build/rofl/features/rest#authenticated-transaction-submission
        """
        payload = {
            "tx": {
                "kind": "eth",
                "data": {
                    "gas_limit": tx["gas"],
                    "to": tx["to"].lstrip("0x"),
                    "value": tx["value"],
                    "data": tx["data"].lstrip("0x"),
                },
            },
            "encrypt": False,
        }

        path = '/rofl/v1/tx/sign-submit'
        return self._appd_post(path, payload)
    
    def submit_authenticated_tx(self, to_address: str, data: str, value: int = 0) -> Dict:
        """
        Submit authenticated transaction via ROFL (legacy method).
        
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