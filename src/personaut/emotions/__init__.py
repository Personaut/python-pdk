"""Emotion system for Personaut PDK.

This module provides the complete emotion modeling system, including:
- 36 distinct emotions organized into 6 categories
- EmotionalState class for tracking emotion intensities
- Category-based emotion organization and analysis
- Utility functions for emotion validation and lookup

The emotion system is based on a validated emotional taxonomy that provides
comprehensive coverage of human emotional states.

Example:
    >>> from personaut.emotions import EmotionalState, EmotionCategory, ANXIOUS
    >>> state = EmotionalState()
    >>> state.change_emotion(ANXIOUS, 0.8)
    >>> print(state.get_dominant())
    ('anxious', 0.8)
"""

from personaut.emotions.categories import (
    CATEGORY_EMOTIONS,
    EmotionCategory,
    get_category,
    get_emotions_in_category,
    get_negative_emotions,
    get_positive_emotions,
    parse_category,
)
from personaut.emotions.emotion import (
    ALL_EMOTIONS,
    ANGER_EMOTIONS,
    ANGRY,
    ANXIOUS,
    APATHETIC,
    APPRECIATED,
    ASHAMED,
    BORED,
    CHEERFUL,
    CONFUSED,
    CONTENT,
    CREATIVE,
    CRITICAL,
    DEPRESSED,
    EMOTION_METADATA,
    ENERGETIC,
    EXCITED,
    FAITHFUL,
    FEAR_EMOTIONS,
    GUILTY,
    HATEFUL,
    HELPLESS,
    HOPEFUL,
    HOSTILE,
    HURT,
    IMPORTANT,
    INSECURE,
    INTIMATE,
    JOY_EMOTIONS,
    LONELY,
    LOVING,
    NURTURING,
    PEACEFUL_EMOTIONS,
    POWERFUL_EMOTIONS,
    PROUD,
    REJECTED,
    RESPECTED,
    SAD_EMOTIONS,
    SATISFIED,
    SELFISH,
    SENSUAL,
    SUBMISSIVE,
    THOUGHTFUL,
    TRUSTING,
    Emotion,
    get_emotion_metadata,
    is_valid_emotion,
)
from personaut.emotions.state import EmotionalState


__all__ = [
    # Collections
    "ALL_EMOTIONS",
    "ANGER_EMOTIONS",
    # All 36 emotion constants - Anger
    "ANGRY",
    # Fear
    "ANXIOUS",
    # Sad
    "APATHETIC",
    # Powerful
    "APPRECIATED",
    "ASHAMED",
    "BORED",
    "CATEGORY_EMOTIONS",
    # Joy
    "CHEERFUL",
    "CONFUSED",
    # Peaceful
    "CONTENT",
    "CREATIVE",
    "CRITICAL",
    "DEPRESSED",
    "EMOTION_METADATA",
    "ENERGETIC",
    "EXCITED",
    "FAITHFUL",
    "FEAR_EMOTIONS",
    "GUILTY",
    "HATEFUL",
    "HELPLESS",
    "HOPEFUL",
    "HOSTILE",
    "HURT",
    "IMPORTANT",
    "INSECURE",
    "INTIMATE",
    "JOY_EMOTIONS",
    "LONELY",
    "LOVING",
    "NURTURING",
    "PEACEFUL_EMOTIONS",
    "POWERFUL_EMOTIONS",
    "PROUD",
    "REJECTED",
    "RESPECTED",
    "SAD_EMOTIONS",
    "SATISFIED",
    "SELFISH",
    "SENSUAL",
    "SUBMISSIVE",
    "THOUGHTFUL",
    "TRUSTING",
    # Emotion dataclass
    "Emotion",
    # Category enum
    "EmotionCategory",
    # Main class
    "EmotionalState",
    # Functions
    "get_category",
    "get_emotion_metadata",
    "get_emotions_in_category",
    "get_negative_emotions",
    "get_positive_emotions",
    "is_valid_emotion",
    "parse_category",
]
