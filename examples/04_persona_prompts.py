#!/usr/bin/env python3
"""Example 04: Persona-Driven LLM Generation (Offline Demo)

This example demonstrates how Personaut constructs prompts from persona
data (traits, emotions, etc.) to generate in-character LLM responses.

This shows the OFFLINE workflow - the prompt construction without actually
calling an LLM. For live generation, see 05_llm_generation.py.
"""

from personaut import create_individual
from personaut.prompts import PromptBuilder


def main() -> None:
    print("=" * 60)
    print("Example 04: Persona-Driven LLM Generation (Offline)")
    print("=" * 60)

    # 1. Create a persona with personality
    print("\n1. Creating persona with personality...")
    sarah = create_individual(
        name="Sarah",
        traits={
            "warmth": 0.9,       # Very warm and friendly
            "liveliness": 0.8,   # Energetic and expressive
            "sensitivity": 0.7,  # Emotionally attuned
            "dominance": 0.3,    # Not dominant, more collaborative
        },
        emotional_state={
            "cheerful": 0.7,     # Currently feeling cheerful
            "hopeful": 0.5,      # And hopeful
        },
        metadata={
            "occupation": "barista",
            "interests": "coffee and art",
            "speaking_style": "warm, uses coffee metaphors",
        },
    )
    print(f"   Created: {sarah.name}")
    print(f"   Warmth: {sarah.get_trait('warmth')}")
    print(f"   Dominant emotion: {sarah.get_dominant_emotion()}")

    # 2. Show how traits influence prompts
    print("\n2. How Traits Influence Prompts:")
    print("   High WARMTH (0.9) suggests:")
    print("   - Use friendly, welcoming language")
    print("   - Show empathy and understanding")
    print("   - Be supportive and encouraging")
    print("")
    print("   High LIVELINESS (0.8) suggests:")
    print("   - Use energetic, expressive language")
    print("   - Include enthusiasm in responses")
    print("   - Be animated and engaging")
    print("")
    print("   Low DOMINANCE (0.3) suggests:")
    print("   - Be collaborative, not commanding")
    print("   - Ask questions rather than dictate")
    print("   - Show openness to others' ideas")

    # 3. Show how emotions influence prompts
    print("\n3. How Emotions Influence Prompts:")
    emotions = sarah.get_emotional_state().to_dict()
    active = {k: v for k, v in emotions.items() if v > 0}
    print(f"   Active emotions: {active}")
    print("")
    print("   CHEERFUL (0.7) means:")
    print("   - Positive, upbeat tone")
    print("   - Likely to use humor or lightness")
    print("   - Optimistic framing")
    print("")
    print("   HOPEFUL (0.5) means:")
    print("   - Forward-looking perspective")
    print("   - Encouraging about possibilities")
    print("   - Open to positive outcomes")

    # 4. Construct a system prompt from persona
    print("\n4. Constructing System Prompt from Persona:")

    # This is what Personaut does internally to create prompts
    trait_desc = []
    if sarah.get_trait("warmth") > 0.7:
        trait_desc.append("warm and friendly")
    if sarah.get_trait("liveliness") > 0.7:
        trait_desc.append("energetic and expressive")
    if sarah.get_trait("sensitivity") > 0.6:
        trait_desc.append("emotionally attuned")
    if sarah.get_trait("dominance") < 0.4:
        trait_desc.append("collaborative and supportive")

    emotion_desc = []
    if sarah.emotional_state.get_emotion("cheerful") > 0.5:
        emotion_desc.append("cheerful and upbeat")
    if sarah.emotional_state.get_emotion("hopeful") > 0.3:
        emotion_desc.append("hopeful about the future")

    system_prompt = f"""You are {sarah.name}, a {sarah.get_metadata('occupation')}.

Your personality is: {', '.join(trait_desc)}.
You're interested in: {sarah.get_metadata('interests')}.
Speaking style: {sarah.get_metadata('speaking_style')}.

Current mood: You're feeling {', '.join(emotion_desc)}.

Respond naturally as this character. Keep responses conversational."""

    print("-" * 50)
    print(system_prompt)
    print("-" * 50)

    # 5. Show contrast with different persona
    print("\n5. Compare: Different Persona, Different Prompt")

    mike = create_individual(
        name="Mike",
        traits={
            "warmth": 0.4,       # More reserved
            "liveliness": 0.3,  # Calm and measured
            "reasoning": 0.9,   # Highly analytical
            "dominance": 0.7,   # More assertive
        },
        emotional_state={
            "content": 0.5,
            "thoughtful": 0.6,
        },
        metadata={
            "occupation": "software architect",
            "interests": "systems design and efficiency",
            "speaking_style": "precise, technical, logical",
        },
    )

    trait_desc2 = []
    if mike.get_trait("reasoning") > 0.7:
        trait_desc2.append("analytical and logical")
    if mike.get_trait("dominance") > 0.6:
        trait_desc2.append("direct and decisive")
    if mike.get_trait("warmth") < 0.5:
        trait_desc2.append("professionally reserved")

    system_prompt2 = f"""You are {mike.name}, a {mike.get_metadata('occupation')}.

Your personality is: {', '.join(trait_desc2)}.
You're interested in: {mike.get_metadata('interests')}.
Speaking style: {mike.get_metadata('speaking_style')}.

Respond naturally as this character. Keep responses professional and precise."""

    print("-" * 50)
    print(system_prompt2)
    print("-" * 50)

    # 6. Show same input, different responses expected
    print("\n6. Same Input, Different Expected Responses:")
    user_input = "How's your day going?"
    print(f"   User: '{user_input}'")
    print("")
    print("   Sarah (warm, cheerful) might say:")
    print("   'Oh, it's been a great morning! Just served the perfect latte")
    print("    to a customer - you know that feeling when the foam is *just right*?'")
    print("")
    print("   Mike (analytical, reserved) might say:")
    print("   'Productive. Finished the architecture review ahead of schedule.")
    print("    The new microservices design is coming together well.'")

    print("\n" + "=" * 60)
    print("✅ Example 04 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: Personaut uses traits and emotions to construct")
    print("system prompts that ensure LLM responses match the persona.")


if __name__ == "__main__":
    main()
