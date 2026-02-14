"""Emotion definitions for Personaut PDK.

This module defines all 36 emotions used in the Personaut emotional modeling
system. Each emotion is categorized into one of six major emotional groups.

The emotion system is based on a validated emotional taxonomy that provides
comprehensive coverage of human emotional states while maintaining clear
distinctions between related emotions.

Example:
    >>> from personaut.emotions.emotion import ANXIOUS, HOPEFUL, ALL_EMOTIONS
    >>> print(f"Tracking {len(ALL_EMOTIONS)} emotions")
    Tracking 36 emotions
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Emotion:
    """Representation of a single emotion type.

    Emotions are immutable data objects that describe a type of
    emotional experience with its name, category, and description.

    Attributes:
        name: Lowercase name of the emotion (e.g., "anxious").
        category: Category the emotion belongs to (e.g., "fear").
        description: Brief description of the emotional state.

    Example:
        >>> emotion = Emotion("anxious", "fear", "Feeling worried or uneasy")
        >>> print(emotion.name)
        anxious
    """

    name: str
    category: str
    description: str

    def __str__(self) -> str:
        """Return the emotion name."""
        return self.name


# =============================================================================
# Anger/Mad Emotions
# =============================================================================

HOSTILE = "hostile"
"""Feeling antagonistic or unfriendly toward others."""

HURT = "hurt"
"""Feeling emotional pain or distress from perceived mistreatment."""

ANGRY = "angry"
"""Feeling strong displeasure or hostility."""

SELFISH = "selfish"
"""Feeling focused on one's own needs at expense of others."""

HATEFUL = "hateful"
"""Feeling intense dislike or ill will."""

CRITICAL = "critical"
"""Feeling inclined to find fault with others."""

# =============================================================================
# Sad/Sadness Emotions
# =============================================================================

GUILTY = "guilty"
"""Feeling responsible for wrongdoing or failure."""

ASHAMED = "ashamed"
"""Feeling embarrassed or disgraced about behavior or circumstances."""

DEPRESSED = "depressed"
"""Feeling deep sadness and lack of hope."""

LONELY = "lonely"
"""Feeling isolated or lacking meaningful connection."""

BORED = "bored"
"""Feeling uninterested or lacking stimulation."""

APATHETIC = "apathetic"
"""Feeling indifferent or lacking emotional engagement."""

# =============================================================================
# Fear/Scared Emotions
# =============================================================================

REJECTED = "rejected"
"""Feeling dismissed or unwanted by others."""

CONFUSED = "confused"
"""Feeling unable to understand or make sense of things."""

SUBMISSIVE = "submissive"
"""Feeling inclined to yield to others' authority."""

INSECURE = "insecure"
"""Feeling uncertain about oneself or one's position."""

ANXIOUS = "anxious"
"""Feeling worried or uneasy about potential threats."""

HELPLESS = "helpless"
"""Feeling unable to act or help oneself."""

# =============================================================================
# Joy/Happiness Emotions
# =============================================================================

EXCITED = "excited"
"""Feeling eager anticipation or enthusiasm."""

SENSUAL = "sensual"
"""Feeling connected to physical pleasures and sensations."""

ENERGETIC = "energetic"
"""Feeling full of vitality and vigor."""

CHEERFUL = "cheerful"
"""Feeling noticeably happy and optimistic."""

CREATIVE = "creative"
"""Feeling inspired and inventive."""

HOPEFUL = "hopeful"
"""Feeling optimistic about future possibilities."""

# =============================================================================
# Powerful/Confident Emotions
# =============================================================================

PROUD = "proud"
"""Feeling satisfaction from achievements or qualities."""

RESPECTED = "respected"
"""Feeling valued and admired by others."""

APPRECIATED = "appreciated"
"""Feeling recognized and valued for contributions."""

IMPORTANT = "important"
"""Feeling significant and consequential."""

FAITHFUL = "faithful"
"""Feeling loyal and devoted to beliefs or relationships."""

SATISFIED = "satisfied"
"""Feeling content with circumstances or outcomes."""

# =============================================================================
# Peaceful/Calm Emotions
# =============================================================================

CONTENT = "content"
"""Feeling peacefully satisfied with things as they are."""

THOUGHTFUL = "thoughtful"
"""Feeling reflective and considerate."""

INTIMATE = "intimate"
"""Feeling closely connected and personal with others."""

LOVING = "loving"
"""Feeling deep affection and care for others."""

TRUSTING = "trusting"
"""Feeling confident in the reliability of others."""

NURTURING = "nurturing"
"""Feeling caring and supportive toward others' growth."""


# =============================================================================
# All Emotions Collection
# =============================================================================

# Anger category
ANGER_EMOTIONS: list[str] = [HOSTILE, HURT, ANGRY, SELFISH, HATEFUL, CRITICAL]
"""All emotions in the Anger/Mad category."""

# Sad category
SAD_EMOTIONS: list[str] = [GUILTY, ASHAMED, DEPRESSED, LONELY, BORED, APATHETIC]
"""All emotions in the Sad/Sadness category."""

# Fear category
FEAR_EMOTIONS: list[str] = [REJECTED, CONFUSED, SUBMISSIVE, INSECURE, ANXIOUS, HELPLESS]
"""All emotions in the Fear/Scared category."""

# Joy category
JOY_EMOTIONS: list[str] = [EXCITED, SENSUAL, ENERGETIC, CHEERFUL, CREATIVE, HOPEFUL]
"""All emotions in the Joy/Happiness category."""

# Powerful category
POWERFUL_EMOTIONS: list[str] = [PROUD, RESPECTED, APPRECIATED, IMPORTANT, FAITHFUL, SATISFIED]
"""All emotions in the Powerful/Confident category."""

# Peaceful category
PEACEFUL_EMOTIONS: list[str] = [CONTENT, THOUGHTFUL, INTIMATE, LOVING, TRUSTING, NURTURING]
"""All emotions in the Peaceful/Calm category."""

# Complete list of all 36 emotions
ALL_EMOTIONS: list[str] = [
    # Anger
    HOSTILE,
    HURT,
    ANGRY,
    SELFISH,
    HATEFUL,
    CRITICAL,
    # Sad
    GUILTY,
    ASHAMED,
    DEPRESSED,
    LONELY,
    BORED,
    APATHETIC,
    # Fear
    REJECTED,
    CONFUSED,
    SUBMISSIVE,
    INSECURE,
    ANXIOUS,
    HELPLESS,
    # Joy
    EXCITED,
    SENSUAL,
    ENERGETIC,
    CHEERFUL,
    CREATIVE,
    HOPEFUL,
    # Powerful
    PROUD,
    RESPECTED,
    APPRECIATED,
    IMPORTANT,
    FAITHFUL,
    SATISFIED,
    # Peaceful
    CONTENT,
    THOUGHTFUL,
    INTIMATE,
    LOVING,
    TRUSTING,
    NURTURING,
]
"""Complete list of all 36 emotions in the system."""


# Emotion metadata registry
EMOTION_METADATA: dict[str, Emotion] = {
    # Anger
    HOSTILE: Emotion(HOSTILE, "anger", "Feeling antagonistic or unfriendly toward others"),
    HURT: Emotion(HURT, "anger", "Feeling emotional pain from perceived mistreatment"),
    ANGRY: Emotion(ANGRY, "anger", "Feeling strong displeasure or hostility"),
    SELFISH: Emotion(SELFISH, "anger", "Focused on one's own needs at expense of others"),
    HATEFUL: Emotion(HATEFUL, "anger", "Feeling intense dislike or ill will"),
    CRITICAL: Emotion(CRITICAL, "anger", "Inclined to find fault with others"),
    # Sad
    GUILTY: Emotion(GUILTY, "sad", "Feeling responsible for wrongdoing or failure"),
    ASHAMED: Emotion(ASHAMED, "sad", "Feeling embarrassed about behavior or circumstances"),
    DEPRESSED: Emotion(DEPRESSED, "sad", "Feeling deep sadness and lack of hope"),
    LONELY: Emotion(LONELY, "sad", "Feeling isolated or lacking meaningful connection"),
    BORED: Emotion(BORED, "sad", "Feeling uninterested or lacking stimulation"),
    APATHETIC: Emotion(APATHETIC, "sad", "Feeling indifferent or lacking engagement"),
    # Fear
    REJECTED: Emotion(REJECTED, "fear", "Feeling dismissed or unwanted by others"),
    CONFUSED: Emotion(CONFUSED, "fear", "Unable to understand or make sense of things"),
    SUBMISSIVE: Emotion(SUBMISSIVE, "fear", "Inclined to yield to others' authority"),
    INSECURE: Emotion(INSECURE, "fear", "Uncertain about oneself or one's position"),
    ANXIOUS: Emotion(ANXIOUS, "fear", "Feeling worried about potential threats"),
    HELPLESS: Emotion(HELPLESS, "fear", "Feeling unable to act or help oneself"),
    # Joy
    EXCITED: Emotion(EXCITED, "joy", "Feeling eager anticipation or enthusiasm"),
    SENSUAL: Emotion(SENSUAL, "joy", "Connected to physical pleasures and sensations"),
    ENERGETIC: Emotion(ENERGETIC, "joy", "Feeling full of vitality and vigor"),
    CHEERFUL: Emotion(CHEERFUL, "joy", "Feeling noticeably happy and optimistic"),
    CREATIVE: Emotion(CREATIVE, "joy", "Feeling inspired and inventive"),
    HOPEFUL: Emotion(HOPEFUL, "joy", "Feeling optimistic about future possibilities"),
    # Powerful
    PROUD: Emotion(PROUD, "powerful", "Satisfaction from achievements or qualities"),
    RESPECTED: Emotion(RESPECTED, "powerful", "Feeling valued and admired by others"),
    APPRECIATED: Emotion(APPRECIATED, "powerful", "Recognized and valued for contributions"),
    IMPORTANT: Emotion(IMPORTANT, "powerful", "Feeling significant and consequential"),
    FAITHFUL: Emotion(FAITHFUL, "powerful", "Loyal and devoted to beliefs or relationships"),
    SATISFIED: Emotion(SATISFIED, "powerful", "Feeling content with outcomes"),
    # Peaceful
    CONTENT: Emotion(CONTENT, "peaceful", "Peacefully satisfied with things as they are"),
    THOUGHTFUL: Emotion(THOUGHTFUL, "peaceful", "Feeling reflective and considerate"),
    INTIMATE: Emotion(INTIMATE, "peaceful", "Closely connected and personal with others"),
    LOVING: Emotion(LOVING, "peaceful", "Feeling deep affection and care for others"),
    TRUSTING: Emotion(TRUSTING, "peaceful", "Confident in the reliability of others"),
    NURTURING: Emotion(NURTURING, "peaceful", "Caring and supportive toward others' growth"),
}
"""Metadata for all emotions including category and description."""


def get_emotion_metadata(emotion: str) -> Emotion:
    """Get metadata for an emotion.

    Args:
        emotion: Name of the emotion (lowercase).

    Returns:
        Emotion object with name, category, and description.

    Raises:
        KeyError: If the emotion is not recognized.

    Example:
        >>> metadata = get_emotion_metadata("anxious")
        >>> print(metadata.category)
        fear
    """
    return EMOTION_METADATA[emotion]


def is_valid_emotion(emotion: str) -> bool:
    """Check if an emotion name is valid.

    Args:
        emotion: Name to check.

    Returns:
        True if the emotion is recognized, False otherwise.

    Example:
        >>> is_valid_emotion("anxious")
        True
        >>> is_valid_emotion("happiness")
        False
    """
    return emotion in ALL_EMOTIONS


__all__ = [
    # Collections
    "ALL_EMOTIONS",
    "ANGER_EMOTIONS",
    # Anger emotions
    "ANGRY",
    # Fear emotions
    "ANXIOUS",
    # Sad emotions
    "APATHETIC",
    # Powerful emotions
    "APPRECIATED",
    "ASHAMED",
    "BORED",
    # Joy emotions
    "CHEERFUL",
    "CONFUSED",
    # Peaceful emotions
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
    # Classes
    "Emotion",
    # Functions
    "get_emotion_metadata",
    "is_valid_emotion",
]
