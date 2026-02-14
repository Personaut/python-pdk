#!/usr/bin/env python3
"""Example 05: Live LLM Generation with Personas

This example demonstrates actual LLM generation with personality-driven
responses. Requires an API key (GOOGLE_API_KEY or AWS credentials).

Usage:
    GOOGLE_API_KEY=your_key python 05_llm_generation.py
"""

import os
import sys

from personaut import create_individual
from personaut.models import get_llm, Provider


def build_system_prompt(individual) -> str:
    """Build a system prompt from an individual's persona data."""
    trait_desc = []
    if individual.get_trait("warmth") > 0.7:
        trait_desc.append("warm and friendly")
    if individual.get_trait("liveliness") > 0.7:
        trait_desc.append("energetic and expressive")
    if individual.get_trait("sensitivity") > 0.6:
        trait_desc.append("emotionally attuned")
    if individual.get_trait("dominance") < 0.4:
        trait_desc.append("collaborative")
    if individual.get_trait("reasoning") > 0.7:
        trait_desc.append("analytical and logical")
    if individual.get_trait("dominance") > 0.6:
        trait_desc.append("direct and decisive")

    emotion_desc = []
    emotions = individual.get_emotional_state().to_dict()
    for emotion, value in emotions.items():
        if value > 0.5:
            emotion_desc.append(emotion)

    personality = ", ".join(trait_desc) if trait_desc else "balanced"
    mood = ", ".join(emotion_desc) if emotion_desc else "neutral"

    occupation = individual.get_metadata("occupation") or "person"
    interests = individual.get_metadata("interests") or "various things"
    speaking_style = individual.get_metadata("speaking_style") or "natural"

    return f"""You are {individual.name}, a {occupation}.

Your personality is: {personality}.
You're interested in: {interests}.
Speaking style: {speaking_style}.
Current mood: {mood}.

Respond naturally as this character. Keep responses to 2-3 sentences."""


def main() -> None:
    print("=" * 60)
    print("Example 05: Live LLM Generation with Personas")
    print("=" * 60)

    # Check for API credentials
    has_gemini = bool(os.environ.get("GOOGLE_API_KEY"))
    has_bedrock = bool(os.environ.get("AWS_ACCESS_KEY_ID"))

    if not (has_gemini or has_bedrock):
        print("\n⚠️  No API credentials found!")
        print("   Set GOOGLE_API_KEY for Gemini, or")
        print("   Set AWS credentials for Bedrock")
        print("\n   Run example 04 for the offline demo.")
        return

    # Use available provider
    if has_gemini:
        provider = Provider.GEMINI
        print(f"\nUsing provider: Gemini")
    else:
        provider = Provider.BEDROCK
        print(f"\nUsing provider: Bedrock")

    llm = get_llm(provider)

    # 1. Create Sarah - warm, cheerful barista
    print("\n1. Creating Personas...")
    sarah = create_individual(
        name="Sarah",
        traits={"warmth": 0.9, "liveliness": 0.8, "sensitivity": 0.7, "dominance": 0.3},
        emotional_state={"cheerful": 0.7, "hopeful": 0.5},
        metadata={
            "occupation": "barista",
            "interests": "coffee, latte art, and local art galleries",
            "speaking_style": "warm, friendly, uses coffee metaphors",
        },
    )
    print(f"   Created: {sarah.name} (warm barista)")

    # 2. Create Mike - analytical software architect
    mike = create_individual(
        name="Mike",
        traits={"warmth": 0.4, "liveliness": 0.3, "reasoning": 0.9, "dominance": 0.7},
        emotional_state={"content": 0.5},
        metadata={
            "occupation": "software architect",
            "interests": "systems design, optimization, and chess",
            "speaking_style": "precise, technical, gets to the point",
        },
    )
    print(f"   Created: {mike.name} (analytical architect)")

    # 3. Same question, different personas
    user_message = "How's your day going?"
    print(f"\n2. User asks: '{user_message}'")

    # Sarah's response
    sarah_prompt = build_system_prompt(sarah)
    print("\n   --- Sarah's Response ---")
    sarah_response = llm.generate(user_message, system=sarah_prompt, temperature=0.7)
    print(f"   {sarah_response}")

    # Mike's response
    mike_prompt = build_system_prompt(mike)
    print("\n   --- Mike's Response ---")
    mike_response = llm.generate(user_message, system=mike_prompt, temperature=0.7)
    print(f"   {mike_response}")

    # 4. Different question
    user_message2 = "What do you think about artificial intelligence?"
    print(f"\n3. User asks: '{user_message2}'")

    print("\n   --- Sarah's Response ---")
    sarah_response2 = llm.generate(user_message2, system=sarah_prompt, temperature=0.7)
    print(f"   {sarah_response2}")

    print("\n   --- Mike's Response ---")
    mike_response2 = llm.generate(user_message2, system=mike_prompt, temperature=0.7)
    print(f"   {mike_response2}")

    # 5. Show emotion change affecting response
    print("\n4. Emotion Change Demo:")
    print("   Changing Sarah's mood to anxious...")
    sarah.change_emotion("cheerful", -0.4)
    sarah.change_emotion("anxious", 0.6)
    new_prompt = build_system_prompt(sarah)

    print(f"\n   User asks: '{user_message}'")
    print("\n   --- Sarah (now anxious) ---")
    anxious_response = llm.generate(user_message, system=new_prompt, temperature=0.7)
    print(f"   {anxious_response}")

    print("\n" + "=" * 60)
    print("✅ Example 05 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: Same question, different personalities = different responses!")


if __name__ == "__main__":
    main()
