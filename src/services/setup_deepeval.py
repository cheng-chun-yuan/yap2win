#!/usr/bin/env python3
"""
Setup script for DeepEval integration.
Helps users configure the AI-powered scoring system.
"""

import os
import sys
import subprocess
from pathlib import Path
from config.config import DEEPEVAL_CONFIG

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_openai_key():
    """Check if OpenAI API key is set."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OpenAI API key found in environment")
        return True
    else:
        print("❌ OpenAI API key not found in environment")
        return False

def setup_env_file():
    """Create or update .env file."""
    env_file = Path(".env")
    
    # Read existing .env file if it exists
    existing_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_vars[key] = value
    
    # Get bot token
    bot_token = existing_vars.get('TOKEN', '')
    if not bot_token:
        bot_token = input("Enter your Telegram bot token: ").strip()
    
    # Get OpenAI API key
    openai_key = existing_vars.get('OPENAI_API_KEY', '')
    if not openai_key:
        openai_key = input("Enter your OpenAI API key: ").strip()
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(f"TOKEN={bot_token}\n")
        f.write(f"OPENAI_API_KEY={openai_key}\n")
    
    print("✅ .env file created/updated successfully!")
    return True

def test_deepeval():
    """Test the DeepEval integration."""
    print("\n🧪 Testing DeepEval integration...")
    try:
        result = subprocess.run([sys.executable, "test_deepeval.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ DeepEval integration test passed!")
            return True
        else:
            print("❌ DeepEval integration test failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ DeepEval test timed out (60 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error running DeepEval test: {e}")
        return False

def show_next_steps():
    """Show next steps for the user."""
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the bot: python bot.py")
    print("2. Add the bot to your Telegram groups")
    print("3. Use /init in a group to start listening")
    print("4. Use /set in private chat to configure rewards")
    print("\nFor more information, see DEEPEVAL_INTEGRATION.md")

def main():
    """Main setup function."""
    print("🚀 DeepEval Integration Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment variables
    setup_env_file()
    
    # Test the integration
    if not test_deepeval():
        print("\n⚠️  DeepEval test failed, but setup can continue.")
        print("The bot will use fallback scoring if AI is unavailable.")
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main() 