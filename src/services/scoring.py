"""
Scoring module for message analysis and point calculation.
"""

from typing import Dict, Any
from config.config import (
    MAX_SCORE, ENGAGEMENT_WORDS, SCORE_WEIGHTS, 
    MESSAGE_LENGTH_THRESHOLD, EXTRA_LENGTH_THRESHOLD
)


class MessageScorer:
    """Handles message scoring logic."""
    
    def __init__(self):
        self.max_score = MAX_SCORE
        self.engagement_words = ENGAGEMENT_WORDS
        self.weights = SCORE_WEIGHTS
    
    def calculate_score(self, text: str, user_info: Dict[str, Any]) -> float:
        """Calculate score for a message based on content and user info."""
        score = 0.0
        
        # Basic scoring based on message length
        if len(text) > MESSAGE_LENGTH_THRESHOLD:
            score += self.weights['base_long_message']
        
        if len(text) > EXTRA_LENGTH_THRESHOLD:
            score += self.weights['extra_long_message']
        
        # Bonus for questions
        if '?' in text:
            score += self.weights['question_bonus']
        
        # Bonus for engagement words
        if any(word in text.lower() for word in self.engagement_words):
            score += self.weights['engagement_bonus']
        
        # Bonus for emojis
        emoji_count = sum(1 for char in text if ord(char) > 127)
        emoji_bonus = min(
            emoji_count * self.weights['emoji_multiplier'], 
            self.weights['emoji_max_bonus']
        )
        score += emoji_bonus
        
        # Cap at maximum score
        return min(score, self.max_score)
    
    def get_emoji_for_score(self, score: float) -> str:
        """Get appropriate emoji based on score."""
        if score >= EMOJI_THRESHOLDS['high']:
            return RESPONSE_EMOJIS['high_score']
        elif score >= EMOJI_THRESHOLDS['medium']:
            return RESPONSE_EMOJIS['medium_score']
        else:
            return RESPONSE_EMOJIS['low_score']
    
    def format_score_message(self, score: float, group_name: str) -> str:
        """Format the score message for user notification."""
        emoji = self.get_emoji_for_score(score)
        return f"{emoji} +{score:.2f} points from {group_name}! Keep engaging to earn more!"


# Global scorer instance
scorer = MessageScorer()