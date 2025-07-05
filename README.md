# Yap2Win Telegram Bot

A Telegram bot that rewards users for engaging in group conversations with points and competitive events.

## Features

- **Message Scoring**: Automatically scores messages based on length, engagement, and content
- **Reward Events**: Pool and rank-based reward events with configurable timeframes
- **Real-time Leaderboards**: Live rankings during active events
- **User Verification**: Simple verification system to prevent spam
- **Multi-group Support**: Manage multiple groups simultaneously
- **Always Active**: Bot always tracks points and sends notifications in all groups
- **Event Control**: Event participation only happens in groups where listening is active

## Commands

### User Commands
- `/help` - Show help message
- `/hello` - Get a greeting
- `/status` - Show your points by group
- `/leaderboard` - Show current event rankings (group only)
- `/reward` or `/rewards` - Show current event information (group only)
- `/result` - Show current standings or final results (group only)

### Admin Commands
- `/init` - Start listening to messages in current group
- `/end` - Stop listening to messages in current group
- `/set` - Set reward configuration (private chat only)

## Recent Updates

### Fixed Issues (Latest)
- ✅ **Fixed `/rewards` command**: Added `/rewards` as an alias for `/reward`
- ✅ **Fixed leaderboard display**: Now properly shows current standings during active events
- ✅ **Added `/result` command**: Shows current standings during events and final results after events
- ✅ **Improved event status checking**: Events now properly check time boundaries
- ✅ **Enhanced user experience**: Better error messages and command feedback
- ✅ **Updated command names**: Changed `/start` to `/init` and `/set_reward` to `/set`
- ✅ **Always active points**: Bot now always tracks points and sends notifications in all groups

### New Features
- 🆕 **Real-time standings**: See current rankings during active events
- 🆕 **Time remaining display**: Shows countdown for active events
- 🆕 **Event status awareness**: Commands now handle different event states (not started, active, finished)
- 🆕 **Better formatting**: Improved display with medals and clear information
- 🆕 **Always active**: Points tracking works in all groups, not just active ones

## Setup

1. Create a `.env` file with your bot token:
```
TOKEN=your_bot_token_here
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the bot:
```bash
python bot.py
```

## Event Types

### Pool Events
- Equal distribution among all participants
- Everyone who participates gets the same reward
- Perfect for encouraging participation

### Rank Events
- Rank-based distribution (1st, 2nd, 3rd place)
- Configurable reward amounts per rank
- Competitive format for top performers

## Usage Examples

### During Active Events
- `/leaderboard` - See current rankings
- `/reward` - See event details and time remaining
- `/result` - See current standings

### After Events End
- `/result` - See final results and winners
- Results are automatically posted when events finish

## Technical Details

- Built with python-telegram-bot
- In-memory data storage (resets on restart)
- Configurable scoring system
- Event-driven architecture

## Setup Instructions

### 1. Get a Telegram Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the token provided by BotFather

### 2. Set Environment Variables

Create a `.env` file in the project root with your bot token:

```bash
# .env
TOKEN=your_actual_telegram_bot_token_here
```

### 3. Authentication for GitHub Container Registry

To pull the Docker image from GitHub Container Registry, you need to authenticate:

#### Option A: Using Personal Access Token (Recommended)

1. Create a GitHub Personal Access Token with `read:packages` scope
2. Login to ghcr.io:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

#### Option B: Using GitHub CLI

```bash
gh auth login
docker login ghcr.io -u USERNAME -p $(gh auth token)
```

### 4. Run the Bot

```bash
# Using Docker Compose
docker-compose up

# Or run locally
python bot.py
```

## Development

To build and run locally:

```bash
# Build the Docker image
docker build -t yap2win-bot .

# Run with environment variable
docker run -e TOKEN=your_token_here yap2win-bot
```

### Admin Setup
- `/init` - Start bot in current group
- `/set` - Configure reward events (in private chat)
- `/end` - Stop bot in current group 