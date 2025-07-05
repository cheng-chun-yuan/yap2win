"""
DeepEval-based scoring module for community engagement evaluation.
Uses LLM-as-a-judge approach to rate content on a 0-10 scale.
"""

import os
import logging
from typing import Dict, Any, Optional
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval
from deepeval.models import GPTModel
from config.config import DEEPEVAL_CONFIG

logger = logging.getLogger(__name__)


class DeepEvalScorer:
    """Handles community engagement scoring using DeepEval LLM-as-a-judge."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the DeepEval scorer."""
        # Set OpenAI API key
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        elif not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize the OpenAI model for direct API calls
        self.model = GPTModel(model="gpt-4-turbo")
        
        # Custom engagement prompt - STRICT SCORING
        self.engagement_prompt = """
        Rate the following message for community engagement on a scale of 0-10.

        STRICT SCORING RULES:
        - ONLY meaningful, unique, and helpful content gets points
        - Simple greetings, acknowledgments, or basic responses get 0 points
        - Must contribute something valuable to the conversation
        - Must be original and thoughtful

        GIVE 0 POINTS FOR:
        - Simple greetings: "ok", "gm", "hello", "hi", "thanks", "good", "nice"
        - Basic acknowledgments: "👍", "okay", "yes", "no", "maybe"
        - Spam or irrelevant content
        - One-word responses
        - Generic responses that don't add value

        GIVE POINTS ONLY FOR:
        - Thoughtful questions that encourage discussion
        - Detailed explanations or insights
        - Helpful advice or information
        - Meaningful responses that build on the conversation
        - Original ideas or perspectives
        - Constructive feedback or suggestions

        Scoring guide:
        0: Simple greetings, basic responses, spam, or non-contributing content
        1-3: Minimal contribution, barely meaningful
        4-6: Somewhat helpful or informative
        7-8: Good contribution with clear value
        9-10: Excellent, highly valuable, and unique contribution

        Message: "{message}"
        User: {username}
        Group: {group_name}

        Rate this message (0-10):"""

    def calculate_score(self, text: str, user_info: Dict[str, Any], group_name: str = "Community") -> float:
        """Calculate engagement score using OpenAI LLM-as-a-judge."""
        try:
            # Get username
            username = user_info.get('username', user_info.get('first_name', 'Unknown'))
            
            # Create custom prompt for this specific message
            custom_prompt = self.engagement_prompt.format(
                message=text,
                username=username,
                group_name=group_name
            )
            
            # Generate response using the model
            response = self.model.generate(custom_prompt)
            
            # Extract score from the response
            score = self._extract_score_from_text(response)
            
            logger.info(f"DeepEval score for user {username}: {score:.2f} for message: {text[:50]}...")
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating DeepEval score: {e}")
            # Fallback to a basic score if DeepEval fails
            return self._fallback_score(text, user_info)
    
    def _extract_score_from_text(self, response: str) -> float:
        """Extract numerical score from model response."""
        try:
            # Try to extract a number from the response
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', str(response))
            
            if numbers:
                score = float(numbers[0])
                # Ensure score is within 0-10 range
                return max(0.0, min(10.0, score))
            else:
                # If no number found, try to parse the response
                response_text = str(response).lower()
                if 'excellent' in response_text or '10' in response_text:
                    return 9.5
                elif 'good' in response_text or '8' in response_text:
                    return 8.0
                elif 'decent' in response_text or '6' in response_text:
                    return 6.0
                elif 'basic' in response_text or '4' in response_text:
                    return 4.0
                else:
                    return 5.0  # Default middle score
                    
        except Exception as e:
            logger.error(f"Error extracting score from response: {e}")
            return 5.0  # Default fallback score
    
    def _fallback_score(self, text: str, user_info: Dict[str, Any]) -> float:
        """Fallback scoring method if DeepEval fails - STRICT SCORING."""
        score = 0.0
        
        # Check for simple greetings and basic responses - GIVE 0 POINTS
        simple_greetings = [
            'ok', 'okay', 'gm', 'gn', 'hello', 'hi', 'hey', 'thanks', 'thank you',
            'good', 'nice', 'cool', 'awesome', 'great', 'yes', 'no', 'maybe',
            '👍', '👎', '😊', '😄', 'lol', 'haha', 'wow', 'omg'
        ]
        
        text_lower = text.lower().strip()
        
        # If it's just a simple greeting or basic response, give 0 points
        if text_lower in simple_greetings or len(text.strip()) <= 3:
            return 0.0
        
        # Check if it's just emojis or very short
        if len(text.strip()) <= 5 and not any(c.isalpha() for c in text):
            return 0.0
        
        # Only give points for meaningful content
        if len(text) > 20:  # Must be substantial
            score += 1.0
        
        if len(text) > 50:  # Must be detailed
            score += 2.0
        
        # Bonus for questions (but only if substantial)
        if '?' in text and len(text) > 15:
            score += 1.5
        
        # Bonus for meaningful words (but not simple ones)
        meaningful_words = ['explain', 'discuss', 'think', 'opinion', 'experience', 'suggest', 'help', 'understand']
        if any(word in text_lower for word in meaningful_words):
            score += 1.0
        
        # Penalty for too many emojis (indicates low effort)
        emoji_count = sum(1 for char in text if ord(char) > 127)
        if emoji_count > 3:
            score -= 1.0
        
        # Cap at maximum score and ensure minimum is 0
        return max(0.0, min(score, 10.0))
    
    def get_emoji_for_score(self, score: float) -> str:
        """Get appropriate emoji based on score."""
        if score >= 8.0:
            return "🎉"  # High engagement
        elif score >= 6.0:
            return "🎯"  # Good engagement
        elif score >= 4.0:
            return "✨"  # Decent engagement
        else:
            return "💬"  # Basic engagement
    
    def format_score_message(self, score: float, group_name: str) -> str:
        """Format the score message for user notification."""
        emoji = self.get_emoji_for_score(score)
        return f"{emoji} +{score:.2f} points from {group_name}! Keep engaging to earn more!"


# Global DeepEval scorer instance
deepeval_scorer = DeepEvalScorer() 