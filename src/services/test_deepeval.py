#!/usr/bin/env python3
"""
Test script for DeepEval scoring system.
"""

import os
import sys
from services.deepeval_scoring import DeepEvalScorer
from config.config import DEEPEVAL_CONFIG

def test_deepeval_scoring():
    """Test the DeepEval scoring system with sample messages."""
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    try:
        # Initialize the scorer
        print("🤖 Initializing DeepEval scorer...")
        scorer = DeepEvalScorer()
        print("✅ DeepEval scorer initialized successfully!")
        
        # Test messages with different engagement levels - STRICT SCORING
        test_messages = [
            {
                "text": "I think we should consider the long-term implications of this approach. Based on my experience, it could lead to better outcomes because...",
                "user_info": {"username": "thoughtful_user", "first_name": "Thoughtful"},
                "expected_score": "high"
            },
            {
                "text": "What do you think about this topic? I'd love to hear different perspectives and understand how others approach this problem.",
                "user_info": {"username": "curious_user", "first_name": "Curious"},
                "expected_score": "high"
            },
            {
                "text": "This is an interesting point. I'd like to discuss how this could be implemented in practice.",
                "user_info": {"username": "discussion_user", "first_name": "Discussion"},
                "expected_score": "medium"
            },
            {
                "text": "ok",
                "user_info": {"username": "short_user", "first_name": "Short"},
                "expected_score": "zero"
            },
            {
                "text": "gm",
                "user_info": {"username": "greeting_user", "first_name": "Greeting"},
                "expected_score": "zero"
            },
            {
                "text": "👍",
                "user_info": {"username": "emoji_user", "first_name": "Emoji"},
                "expected_score": "zero"
            },
            {
                "text": "thanks",
                "user_info": {"username": "thanks_user", "first_name": "Thanks"},
                "expected_score": "zero"
            },
            {
                "text": "SPAM SPAM SPAM BUY NOW!!!",
                "user_info": {"username": "spam_user", "first_name": "Spam"},
                "expected_score": "zero"
            }
        ]
        
        print("\n🧪 Testing DeepEval scoring with sample messages...")
        print("=" * 60)
        
        for i, test_case in enumerate(test_messages, 1):
            print(f"\nTest {i}: {test_case['expected_score'].upper()} engagement expected")
            print(f"Message: {test_case['text']}")
            
            try:
                score = scorer.calculate_score(
                    test_case['text'], 
                    test_case['user_info'], 
                    "Test Group"
                )
                
                emoji = scorer.get_emoji_for_score(score)
                print(f"Score: {score:.2f} {emoji}")
                
                # Validate score range and expectations
                if 0 <= score <= 10:
                    print("✅ Score is within valid range (0-10)")
                    
                    # Check if score matches expectation
                    if test_case['expected_score'] == 'zero' and score == 0:
                        print("✅ Correctly scored as 0 (simple greeting/basic response)")
                    elif test_case['expected_score'] == 'high' and score >= 7:
                        print("✅ Correctly scored as high engagement")
                    elif test_case['expected_score'] == 'medium' and 4 <= score <= 6:
                        print("✅ Correctly scored as medium engagement")
                    else:
                        print(f"⚠️  Score {score:.2f} doesn't match expected {test_case['expected_score']} level")
                else:
                    print("❌ Score is outside valid range!")
                    
            except Exception as e:
                print(f"❌ Error scoring message: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 DeepEval scoring test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing DeepEval scorer: {e}")
        return False

def test_fallback_scoring():
    """Test the fallback scoring when DeepEval fails."""
    print("\n🔄 Testing fallback scoring...")
    
    # Create scorer without OpenAI API key to trigger fallback
    scorer = DeepEvalScorer()
    
    test_message = "This is a test message with some engagement words like thanks and great!"
    user_info = {"username": "fallback_user", "first_name": "Fallback"}
    
    try:
        score = scorer._fallback_score(test_message, user_info)
        print(f"Fallback score: {score:.2f}")
        
        if 0 <= score <= 10:
            print("✅ Fallback scoring works correctly")
            return True
        else:
            print("❌ Fallback score is outside valid range")
            return False
            
    except Exception as e:
        print(f"❌ Error in fallback scoring: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DeepEval Scoring System Test")
    print("=" * 40)
    
    # Test main DeepEval scoring
    main_test_passed = test_deepeval_scoring()
    
    # Test fallback scoring
    fallback_test_passed = test_fallback_scoring()
    
    print("\n" + "=" * 40)
    if main_test_passed and fallback_test_passed:
        print("🎉 All tests passed! DeepEval integration is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1) 