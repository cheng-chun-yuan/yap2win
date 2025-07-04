# Yap2Win Telegram Bot

A simple Telegram bot built with python-telegram-bot.

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