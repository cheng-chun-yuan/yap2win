# DeepEval Integration for Community Engagement Scoring

This document explains how the Telegram bot now uses DeepEval with LLM-as-a-Judge approach to automatically rate community engagement on a 0-10 scale.

## Overview

The bot has been upgraded from a simple rule-based scoring system to an AI-powered DeepEval scoring system that uses GPT-4 to evaluate message quality and community engagement.

## Key Features

- **AI-Powered Scoring**: Uses GPT-4 to evaluate messages on a 0-10 scale
- **Community Engagement Focus**: Considers factors like discussion encouragement, inclusivity, and helpfulness
- **Fallback System**: Falls back to rule-based scoring if AI evaluation fails
- **Customizable Prompts**: Easy to modify the evaluation criteria
- **Real-time Scoring**: Messages are scored immediately when sent

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set OpenAI API Key**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```
   
   Or add it to your `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

## How It Works

### Scoring Process

1. **Message Reception**: Bot receives a message in a group
2. **AI Evaluation**: DeepEval sends the message to GPT-4 with a custom prompt
3. **Score Extraction**: The AI response is parsed to extract a 0-10 score
4. **Fallback**: If AI fails, uses rule-based scoring as backup
5. **Notification**: User receives their score via private message

### Evaluation Criteria

The AI evaluates messages based on:

- **Encourages discussion and interaction**
- **Shows genuine interest in others' opinions**
- **Uses inclusive and welcoming language**
- **Asks thoughtful questions**
- **Provides helpful or informative content**
- **Uses appropriate emojis and tone**
- **Avoids spam, trolling, or negative behavior**
- **Contributes meaningfully to the conversation**

### Scoring Guide

- **0**: Simple greetings, basic responses, spam, or non-contributing content
- **1-3**: Minimal contribution, barely meaningful
- **4-6**: Somewhat helpful or informative
- **7-8**: Good contribution with clear value
- **9-10**: Excellent, highly valuable, and unique contribution

### Zero-Point Messages

The following types of messages will receive 0 points:
- Simple greetings: "ok", "gm", "hello", "hi", "thanks"
- Basic acknowledgments: "👍", "okay", "yes", "no", "maybe"
- One-word responses
- Generic responses that don't add value
- Spam or irrelevant content

## Configuration

### DeepEval Settings

The scoring system can be configured in `config.py`:

```python
DEEPEVAL_CONFIG = {
    'model': 'gpt-4',           # AI model to use
    'max_score': 10.0,          # Maximum possible score
    'fallback_score': 5.0,      # Default score if AI fails
    'engagement_criteria': [...] # List of evaluation criteria
}
```

### Customizing the Prompt

You can modify the evaluation prompt in `deepeval_scoring.py`:

```python
self.engagement_prompt = """
Rate the following message for community engagement on a scale of 0-10.

Consider these factors:
- Your custom criteria here
- More criteria...

Message: "{message}"
User: {username}
Group: {group_name}

Rate this message (0-10):"""
```

## Testing

Run the test script to verify the integration:

```bash
python test_deepeval.py
```

This will test:
- DeepEval initialization
- Sample message scoring
- Fallback scoring system
- Score validation

## Usage Examples

### High Engagement Messages (7-10 points)
- "I think we should consider the long-term implications of this approach. Based on my experience, it could lead to better outcomes because..."
- "What do you think about this topic? I'd love to hear different perspectives and understand how others approach this problem."
- "That's an interesting point! Can you elaborate on how that would work in practice? I'm curious about the implementation details."

### Medium Engagement Messages (4-6 points)
- "This is an interesting point. I'd like to discuss how this could be implemented in practice."
- "I have some experience with this topic. Let me share what I've learned..."
- "This reminds me of a similar situation I encountered. Here's what worked for me..."

### Zero-Point Messages (0 points)
- "ok"
- "gm"
- "👍"
- "thanks"
- "hello"
- "good"
- "nice"
- "SPAM SPAM SPAM BUY NOW!!!"

## Benefits

### For Community Managers
- **Consistent Evaluation**: AI provides consistent scoring across all messages
- **Quality Focus**: Rewards meaningful contributions over spam
- **Engagement Metrics**: Better understanding of community health
- **Automated Moderation**: Helps identify low-quality content

### For Users
- **Fair Scoring**: AI evaluates based on actual engagement quality
- **Immediate Feedback**: Get instant feedback on message quality
- **Learning Opportunity**: Understand what makes good community contributions
- **Recognition**: High-quality contributions are properly rewarded

## Troubleshooting

### Common Issues

1. **OpenAI API Key Not Set**
   ```
   Error: OpenAI API key is required
   Solution: Set OPENAI_API_KEY environment variable
   ```

2. **DeepEval Import Error**
   ```
   Error: No module named 'deepeval'
   Solution: pip install deepeval
   ```

3. **API Rate Limits**
   ```
   Error: Rate limit exceeded
   Solution: The system will automatically fall back to rule-based scoring
   ```

4. **Score Extraction Issues**
   ```
   Error: Could not parse AI response
   Solution: Check the custom prompt format in deepeval_scoring.py
   ```

### Debug Mode

Enable debug logging to see detailed scoring information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- **API Costs**: Each message evaluation costs ~$0.01-0.03 depending on message length
- **Response Time**: AI evaluation adds 1-3 seconds to message processing
- **Rate Limits**: OpenAI has rate limits that may affect high-volume groups
- **Fallback System**: Ensures the bot continues working even if AI is unavailable

## Future Enhancements

- **Batch Processing**: Evaluate multiple messages together to reduce API calls
- **Custom Models**: Support for other LLM providers (Claude, Gemini, etc.)
- **Learning System**: Adapt scoring based on community feedback
- **Advanced Analytics**: Detailed engagement metrics and trends
- **Multi-language Support**: Evaluate messages in different languages

## Support

For issues with the DeepEval integration:

1. Check the troubleshooting section above
2. Run the test script to verify functionality
3. Check the bot logs for detailed error messages
4. Ensure your OpenAI API key has sufficient credits

## Migration from Old System

The old rule-based scoring system has been completely replaced. The new system:

- Maintains the same 0-10 scoring scale
- Uses the same point tracking and reward distribution
- Provides the same user notifications
- Works with existing event configurations

No changes to existing bot commands or user workflows are required. 