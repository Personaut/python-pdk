#!/usr/bin/env python3
"""Example 02: Emotions System

This example demonstrates the 36-emotion system in Personaut PDK,
including emotion categories, states, and manipulation.
"""

from personaut.emotions import (
    # Main class
    EmotionalState,
    # Category enum
    EmotionCategory,
    # All 36 emotions
    ALL_EMOTIONS,
    # Emotion category sets
    JOY_EMOTIONS,
    FEAR_EMOTIONS,
    SAD_EMOTIONS,
    ANGER_EMOTIONS,
    POWERFUL_EMOTIONS,
    PEACEFUL_EMOTIONS,
    # Common emotions
    ANXIOUS,
    CHEERFUL,
    HOPEFUL,
    # Utility functions
    get_category,
    is_valid_emotion,
    get_positive_emotions,
    get_negative_emotions,
)


def main() -> None:
    print("=" * 60)
    print("Example 02: Emotions System")
    print("=" * 60)

    # 1. The 36 emotions organized in 6 categories
    print("\n1. The 36 Emotions in 6 Categories:")
    print(f"   Total emotions: {len(ALL_EMOTIONS)}")
    print(f"   Joy emotions: {len(JOY_EMOTIONS)} - {list(JOY_EMOTIONS)[:3]}...")
    print(f"   Fear emotions: {len(FEAR_EMOTIONS)} - {list(FEAR_EMOTIONS)[:3]}...")
    print(f"   Sad emotions: {len(SAD_EMOTIONS)} - {list(SAD_EMOTIONS)[:3]}...")
    print(f"   Anger emotions: {len(ANGER_EMOTIONS)} - {list(ANGER_EMOTIONS)[:3]}...")
    print(f"   Powerful emotions: {len(POWERFUL_EMOTIONS)} - {list(POWERFUL_EMOTIONS)[:3]}...")
    print(f"   Peaceful emotions: {len(PEACEFUL_EMOTIONS)} - {list(PEACEFUL_EMOTIONS)[:3]}...")

    # 2. Emotion categories
    print("\n2. Emotion Categories:")
    for category in EmotionCategory:
        print(f"   {category.value}")

    # 3. Get emotion category
    print("\n3. Emotion Category Lookup:")
    print(f"   '{CHEERFUL}' -> {get_category(CHEERFUL)}")
    print(f"   '{ANXIOUS}' -> {get_category(ANXIOUS)}")
    print(f"   '{HOPEFUL}' -> {get_category(HOPEFUL)}")

    # 4. Create and manipulate EmotionalState
    print("\n4. Creating EmotionalState:")
    state = EmotionalState()
    print(f"   Initial state: all emotions at 0.0")

    # 5. Change emotions
    print("\n5. Changing Emotions:")
    state.change_emotion(CHEERFUL, 0.8)
    state.change_emotion(HOPEFUL, 0.5)
    state.change_emotion(ANXIOUS, 0.3)
    print(f"   Set cheerful: {state.get_emotion(CHEERFUL)}")
    print(f"   Set hopeful: {state.get_emotion(HOPEFUL)}")
    print(f"   Set anxious: {state.get_emotion(ANXIOUS)}")

    # 6. Get dominant emotion
    print("\n6. Dominant Emotion:")
    dominant = state.get_dominant()
    print(f"   Dominant: {dominant}")

    # 7. Validate emotions
    print("\n7. Validation:")
    print(f"   'cheerful' is valid: {is_valid_emotion('cheerful')}")
    print(f"   'happy' is valid: {is_valid_emotion('happy')}")  # Not in system
    print(f"   ANXIOUS is valid: {is_valid_emotion(ANXIOUS)}")

    # 8. Positive vs Negative emotions
    print("\n8. Positive vs Negative:")
    positives = get_positive_emotions()
    negatives = get_negative_emotions()
    print(f"   Positive emotions: {len(positives)}")
    print(f"   Negative emotions: {len(negatives)}")

    # 9. Export state
    print("\n9. Export State:")
    all_emotions = state.to_dict()
    non_zero = {k: v for k, v in all_emotions.items() if v > 0}
    print(f"   Non-zero emotions: {non_zero}")

    print("\n" + "=" * 60)
    print("✅ Example 02 completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
