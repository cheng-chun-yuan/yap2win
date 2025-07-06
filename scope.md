# Yap2Win - AI-Powered Telegram Engagement Platform

## Product Overview

**Yap2Win** is an intelligent Telegram bot that gamifies community engagement through AI-powered content scoring, reward systems, and blockchain-based incentives. Built on the Oasis ROFL (Remote Oracle Function Layer) for secure wallet management and smart contract interactions.

## Core Technology Stack

### Backend Infrastructure
- **Python 3.x** with python-telegram-bot framework
- **ROFL (Remote Oracle Function Layer)** for secure wallet management
- **Oasis Sapphire** blockchain for smart contract execution
- **DeepEval + GPT-4** for AI-powered content scoring
- **Web3.py** for blockchain interactions

### AI & Scoring Engine
- **DeepEval Framework** with GPT-4 for intelligent content evaluation
- **LLM-as-a-Judge** approach for 0-10 scale scoring
- **Strict Quality Control** - only meaningful content gets points
- **Fallback Scoring System** for AI unavailability

### Blockchain Integration
- **Smart Contract Service** for on-chain reward pool management
- **ROFL Wallet Service** for secure key generation and transaction signing
- **Oasis Sapphire Network** for privacy-preserving smart contracts
- **Ethereum-compatible** wallet address support

## Key Features

### 🤖 AI-Powered Content Scoring
- **Advanced LLM Evaluation**: Uses GPT-4 to assess message quality, uniqueness, and community value
- **Strict Zero-Point System**: Simple greetings like "ok", "gm", "thanks" automatically get 0 points
- **Quality Threshold**: Only meaningful, unique, and helpful content receives points
- **Real-time Scoring**: Immediate AI evaluation of all messages in active groups

### 🎯 Reward System
- **Pool Events**: Equal reward distribution among all participants
- **Rank Events**: Competitive leaderboard with tiered rewards (1st, 2nd, 3rd place)
- **Configurable Timeframes**: Custom start/end times for reward events
- **Real-time Leaderboards**: Live rankings during active events

### 🔐 User Verification System
- **Self.xyz Integration**: Identity verification for age and country requirements
- **NFT Holder Verification**: On-chain verification of specific NFT ownership
- **Wallet Collection**: Ethereum-compatible address collection for rewards
- **Group-specific Rules**: Different verification requirements per group

### 🏦 ROFL Wallet Management
- **Secure Key Generation**: Attested key management via ROFL environment
- **App Authentication**: Unique ROFL app identifier for each bot instance
- **Authenticated Transactions**: Cryptographically signed blockchain transactions
- **Balance Monitoring**: Real-time wallet balance tracking

### 📊 Group Management
- **Multi-group Support**: Manage multiple Telegram groups simultaneously
- **Admin Controls**: Group-specific initialization and configuration
- **Listening Mode**: Selective message processing per group
- **Event Isolation**: Independent reward events per group

## Technical Architecture

### Message Processing Pipeline
1. **Message Ingestion**: Telegram bot receives group messages
2. **AI Evaluation**: DeepEval with GPT-4 scores content on 0-10 scale
3. **Point Assignment**: Qualified messages earn points based on AI score
4. **Leaderboard Update**: Real-time ranking updates during events
5. **Reward Distribution**: Automated payouts at event completion

### Smart Contract Integration
1. **Pool Creation**: On-chain reward pool creation with ROFL signatures
2. **Participant Tracking**: Blockchain-based participant registration
3. **Result Submission**: Cryptographically verified final results
4. **Automated Payouts**: Smart contract-based reward distribution

### Security Features
- **ROFL Attestation**: All wallet operations in secure enclave environment
- **Unix Domain Socket**: Secure communication with ROFL appd
- **Encrypted Transactions**: Privacy-preserving transaction submission
- **Role-based Access**: Admin-only configuration commands

## Command Reference

### User Commands
- `/help` - Display help and current group status
- `/status` - Show personal points by group
- `/leaderboard` - View current event rankings
- `/reward` - Display active event information
- `/result` - Show current standings or final results
- `/verify` - Start user verification process
- `/test` - Test ROFL service connection

### Admin Commands
- `/init` - Start bot listening in current group
- `/end` - Stop bot listening in current group
- `/set` - Configure reward events (private chat only)
- `/new_bot` - Create new ROFL wallet for funding
- `/bot` - Display bot wallet information
- `/set_rule` - Configure group verification rules

## Event Types

### Pool Events
- **Equal Distribution**: All participants receive equal reward shares
- **Participation-based**: Encourages broad community engagement
- **Configurable Amount**: Admin sets total pool size
- **Automatic Payout**: Smart contract handles distribution

### Rank Events
- **Competitive Format**: Leaderboard-based ranking system
- **Tiered Rewards**: Different amounts for 1st, 2nd, 3rd place
- **Merit-based**: Rewards highest-scoring participants
- **Real-time Updates**: Live leaderboard during events

## Deployment Configuration

### ROFL Setup
```yaml
name: yap2win
version: 0.1.0
tee: tdx
kind: container
resources:
  memory: 2048
  cpus: 2
  storage: 10000
```

### Required Environment Variables
- `TOKEN`: Telegram bot token
- `OPENAI_API_KEY`: OpenAI API key for AI scoring
- `CONTRACT_ADDRESS`: Smart contract address for rewards

### Docker Integration
- **Container-based**: Full Docker support with compose.yaml
- **Volume Mounting**: ROFL socket access via volume mounts
- **Environment Management**: Secure secret handling

## Use Cases

### Community Building
- **Engagement Gamification**: Transform passive groups into active communities
- **Quality Control**: AI ensures only valuable content is rewarded
- **Fair Distribution**: Equal opportunity for all participants to earn

### Content Curation
- **AI-Powered Filtering**: Automatic identification of valuable contributions
- **Spam Prevention**: Zero points for low-effort content
- **Discussion Encouragement**: Bonus points for thoughtful questions

### Event Management
- **Time-bounded Competitions**: Configurable start/end times
- **Multiple Formats**: Pool vs rank-based events
- **Automated Administration**: Hands-off event management

## Innovation Highlights

### AI Integration
- **First-of-its-kind**: AI-powered Telegram engagement scoring
- **Strict Quality Standards**: Revolutionary approach to content evaluation
- **Fallback Resilience**: Dual scoring systems for reliability

### Blockchain Security
- **ROFL Innovation**: Cutting-edge secure wallet management
- **Attested Execution**: Cryptographically verified operations
- **Privacy-preserving**: Oasis Sapphire network integration

### User Experience
- **Seamless Onboarding**: Automated group initialization
- **Real-time Feedback**: Immediate scoring and notifications
- **Multi-modal Verification**: Flexible identity verification options

## Future Roadmap

### Short-term Enhancements
- **Advanced Analytics**: Detailed engagement metrics
- **Multi-language Support**: Localized AI scoring
- **Enhanced NFT Integration**: Expanded NFT verification options

### Long-term Vision
- **Cross-platform Expansion**: Discord, Twitter integration
- **DAO Governance**: Community-driven rule configuration
- **Advanced AI Models**: Custom-trained engagement models

## Technical Specifications

### Performance Metrics
- **Message Processing**: Sub-second AI evaluation
- **Concurrent Groups**: Unlimited simultaneous group support
- **Blockchain Latency**: ~5 second transaction confirmation
- **Uptime Target**: 99.9% availability

### Scalability
- **Horizontal Scaling**: Container-based architecture
- **Database Optimization**: In-memory data structures
- **API Rate Limiting**: Intelligent request management
- **Resource Efficiency**: Optimized memory usage

## Security Considerations

### Data Protection
- **Minimal Data Storage**: Only essential information retained
- **Encrypted Communications**: TLS/SSL for all external communications
- **Role-based Access**: Granular permission system
- **Audit Logging**: Comprehensive operation tracking

### Blockchain Security
- **Immutable Records**: All rewards recorded on-chain
- **Cryptographic Signatures**: ROFL-signed transactions
- **Smart Contract Auditing**: Battle-tested contract code
- **Multi-signature Support**: Enhanced security for large pools

---

*This document represents the current state of Yap2Win as of the hackathon submission. The platform demonstrates innovative integration of AI, blockchain, and social engagement technologies.*