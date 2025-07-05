# ROFL Integration for Reward Vault Wallet Management

## Overview
Integrate ROFL (Runtime for On-chain Logic) with the reward vault system to provide secure wallet generation and funding capabilities. This leverages ROFL's authenticated transaction submission and key generation features for secure fund management.

## ROFL Integration Architecture

### 1. ROFL App Setup
**Purpose**: Deploy a ROFL app that handles wallet generation and fund management

**Key Components**:
- **App Identifier**: Unique ROFL app ID for authentication
- **Key Management**: Secure key generation for each reward pool
- **Transaction Signing**: Authenticated transactions for fund transfers
- **API Integration**: REST API for external communication

### 2. Wallet Generation System

#### ROFL App Configuration
```yaml
# rofl.yaml
app_id: "rofl1qqn9xndja7e2pnxhttktmecvwzz0yqwxsquqyxdf"
version: "1.0.0"
runtime: "oasis-core"
```

#### Key Generation Endpoint
**ROFL API**: `/rofl/v1/keys/generate` (POST)

**Request Format**:
```json
{
  "key_id": "reward_pool_001",
  "kind": "secp256k1"
}
```

**Response**:
```json
{
  "key": "a54027bff15a8726b6d9f65383bff20db51c6f3ac5497143a8412a7f16dfdda9"
}
```

### 3. Admin Wallet Creation Flow

#### Step 1: Admin Authentication
```
Admin → Telegram Bot → Verify Admin Status → Generate ROFL Request
```

#### Step 2: Wallet Generation
```
ROFL App → Generate Secp256k1 Key → Create Wallet Address → Store Encrypted
```

#### Step 3: Address Display
```
ROFL App → Return Wallet Address → Display to Admin → Store in Database
```

#### Step 4: Funding Instructions
```
Admin → Receive Funding Address → Fund Wallet → Monitor Balance
```

## Implementation Details

### ROFL App Integration

#### 1. App Identifier Retrieval
**Endpoint**: `/rofl/v1/app/id` (GET)

**Usage**: Retrieve the ROFL app identifier for authentication
```python
import requests

def get_rofl_app_id():
    response = requests.get('http://localhost/rofl/v1/app/id')
    return response.text.strip()
```

#### 2. Wallet Generation Service
```python
class ROFLWalletService:
    def __init__(self, rofl_socket_path="/run/rofl-appd.sock"):
        self.base_url = "http://localhost"
        self.socket_path = rofl_socket_path
    
    def generate_wallet(self, pool_id: str) -> dict:
        """Generate a new wallet for a reward pool"""
        payload = {
            "key_id": f"reward_pool_{pool_id}",
            "kind": "secp256k1"
        }
        
        response = requests.post(
            f"{self.base_url}/rofl/v1/keys/generate",
            json=payload
        )
        
        if response.status_code == 200:
            private_key = response.json()["key"]
            # Derive public address from private key
            wallet_address = self._derive_address(private_key)
            return {
                "pool_id": pool_id,
                "private_key": private_key,
                "address": wallet_address,
                "app_id": self.get_app_id()
            }
        else:
            raise Exception(f"Failed to generate wallet: {response.text}")
    
    def get_app_id(self) -> str:
        """Get the ROFL app identifier"""
        response = requests.get(f"{self.base_url}/rofl/v1/app/id")
        return response.text.strip()
    
    def _derive_address(self, private_key: str) -> str:
        """Derive Ethereum-compatible address from private key"""
        # Implementation for address derivation
        pass
```

### 3. Telegram Bot Integration

#### Admin Commands
```python
class ROFLAdminHandlers:
    @staticmethod
    async def create_funding_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to create a new funding wallet"""
        user = update.effective_user
        
        # Verify admin status
        if not await AdminHandlers.is_admin(update, context):
            await update.message.reply_text("❌ You are not authorized to use this command.")
            return
        
        # Generate wallet using ROFL
        try:
            rofl_service = ROFLWalletService()
            wallet_info = rofl_service.generate_wallet(f"pool_{int(time.time())}")
            
            # Store wallet info securely
            data_storage.store_wallet_info(wallet_info)
            
            # Display funding information
            message = f"""
🏦 **New Funding Wallet Created**

💰 **Wallet Address**: `{wallet_info['address']}`
🔗 **Network**: Oasis Sapphire
📊 **Pool ID**: `{wallet_info['pool_id']}`
🆔 **ROFL App ID**: `{wallet_info['app_id']}`

💡 **Instructions**:
1. Send funds to the wallet address above
2. Use `/check_balance {wallet_info['address']}` to monitor
3. Use `/create_pool {wallet_info['pool_id']}` to start reward pool

⚠️ **Security**: This wallet is managed by ROFL for maximum security
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to create wallet: {str(e)}")
    
    @staticmethod
    async def check_wallet_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check wallet balance"""
        if not context.args:
            await update.message.reply_text("❌ Please provide a wallet address: `/check_balance <address>`")
            return
        
        wallet_address = context.args[0]
        
        try:
            # Query blockchain for balance
            balance = await get_wallet_balance(wallet_address)
            
            message = f"""
💰 **Wallet Balance**

📍 **Address**: `{wallet_address}`
💎 **Balance**: {balance} ROSE
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to check balance: {str(e)}")
```

### 4. Smart Contract Integration

#### ROFL-Authenticated Transactions
```solidity
// RewardVault.sol
contract RewardVault {
    mapping(address => bool) public roflAuthorizedApps;
    
    modifier onlyROFLApp() {
        require(roflAuthorizedApps[msg.sender], "Only ROFL apps authorized");
        _;
    }
    
    function createPoolFromROFL(
        string memory name,
        uint256 amount,
        address fundingWallet
    ) external onlyROFLApp returns (uint256 poolId) {
        // Create pool with ROFL-authenticated funding
        poolId = _createPool(name, amount, fundingWallet);
        emit PoolCreatedFromROFL(poolId, name, amount, fundingWallet);
    }
    
    function transferFromROFLWallet(
        uint256 poolId,
        address recipient,
        uint256 amount
    ) external onlyROFLApp {
        // Transfer funds using ROFL-authenticated transaction
        _transferFunds(poolId, recipient, amount);
    }
}
```

#### ROFL Transaction Submission
```python
class ROFLTransactionService:
    def submit_authenticated_tx(self, to_address: str, data: str, value: int = 0):
        """Submit authenticated transaction via ROFL"""
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
            "http://localhost/rofl/v1/tx/sign-submit",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            raise Exception(f"Transaction failed: {response.text}")
```

## Security Features

### 1. ROFL App Authentication
- **Attested Execution**: ROFL apps run in attested environments
- **Key Persistence**: Generated keys remain consistent across deployments
- **Domain Separation**: Different key IDs for different pools

### 2. Transaction Security
- **Authenticated Transactions**: All transactions signed by ROFL app
- **Encryption**: Transaction data encrypted by default
- **Access Control**: Only authorized ROFL apps can execute functions

### 3. Wallet Management
- **Private Key Security**: Keys generated and stored securely in ROFL
- **Address Derivation**: Public addresses derived from private keys
- **Audit Trail**: All wallet operations logged and encrypted

## Integration Workflow

### 1. Admin Wallet Creation
```
Admin → /create_wallet → ROFL App → Generate Key → Display Address → Store Info
```

### 2. Fund Collection
```
Admin → Fund Wallet → Monitor Balance → Verify Funds → Create Pool
```

### 3. Pool Management
```
ROFL App → Authenticated TX → Create Pool → Manage Funds → Distribute Rewards
```

### 4. Reward Distribution
```
Agent → Trigger Distribution → ROFL App → Sign Transaction → Transfer Funds
```

## Docker Integration

### ROFL App Container
```yaml
# docker-compose.yml
services:
  rofl-app:
    image: ghcr.io/oasisprotocol/rofl-app
    volumes:
      - /run/rofl-appd.sock:/run/rofl-appd.sock
    environment:
      - ROFL_APP_ID=rofl1qqn9xndja7e2pnxhttktmecvwzz0yqwxsquqyxdf
    ports:
      - "8080:8080"
```

### Telegram Bot Integration
```yaml
services:
  telegram-bot:
    build: .
    volumes:
      - ./src:/app/src
    environment:
      - ROFL_SOCKET_PATH=/run/rofl-appd.sock
    depends_on:
      - rofl-app
```

## Benefits of ROFL Integration

### 1. Enhanced Security
- **Attested Execution**: Apps run in trusted environments
- **Key Management**: Secure key generation and storage
- **Transaction Authentication**: Verified app origin

### 2. Simplified Management
- **Automated Wallet Creation**: No manual key management
- **Integrated Funding**: Direct blockchain integration
- **Audit Compliance**: Complete transaction history

### 3. Scalability
- **Multi-Pool Support**: Separate wallets per pool
- **Batch Operations**: Efficient fund management
- **Cross-Chain Ready**: Future expansion capabilities

This integration provides a secure, automated wallet management system for your reward vault, leveraging ROFL's attested execution and authenticated transaction capabilities for maximum security and reliability. 