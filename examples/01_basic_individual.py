#!/usr/bin/env python3
"""Example 01: Basic Individual Creation

This example demonstrates how to create and configure individuals (personas)
in Personaut PDK.
"""

import personaut
from personaut import (
    Individual,
    create_individual,
    create_human,
    create_nontracked_individual,
)


def main() -> None:
    print("=" * 60)
    print("Example 01: Basic Individual Creation")
    print("=" * 60)

    # 1. Create a simulated individual (AI persona)
    print("\n1. Creating a simulated individual...")
    sarah = create_individual(
        name="Sarah",
        traits={"warmth": 0.9, "liveliness": 0.7, "emotional_stability": 0.6},
        emotional_state={"cheerful": 0.6, "hopeful": 0.4},
        metadata={
            "description": "A friendly barista who loves coffee and art. "
            "She's warm, empathetic, and always has a smile.",
            "age": 28,
            "occupation": "barista",
        },
    )
    print(f"   Name: {sarah.name}")
    print(f"   ID: {sarah.id}")

    # 2. Create a human participant (for tracking in simulations)
    print("\n2. Creating a human participant...")
    customer = create_human(
        name="Alex",
        context="A regular customer who visits every morning.",
        role="customer",
    )
    print(f"   Name: {customer.name}")
    print(f"   Is human: {customer.get_metadata('is_human')}")
    print(f"   Role: {customer.get_metadata('role')}")

    # 3. Create a non-tracked entity (for background characters)
    print("\n3. Creating a non-tracked individual...")
    passerby = create_nontracked_individual(role="stranger")
    print(f"   Name: {passerby.name}")
    print(f"   Tracked: {passerby.get_metadata('tracked')}")

    # 4. Get personality traits
    print("\n4. Getting personality traits...")
    print(f"   Warmth: {sarah.get_trait('warmth')}")
    print(f"   Liveliness: {sarah.get_trait('liveliness')}")

    # 5. Set additional traits
    print("\n5. Setting additional traits...")
    sarah.set_trait("sensitivity", 0.8)
    print(f"   Sensitivity: {sarah.get_trait('sensitivity')}")

    # 6. Get emotional state
    print("\n6. Getting emotional state...")
    dominant = sarah.get_dominant_emotion()
    print(f"   Dominant emotion: {dominant}")

    # 7. Change emotional state
    print("\n7. Changing emotional state...")
    sarah.change_emotion("anxious", 0.3)
    print(f"   Added anxiety: {sarah.emotional_state.get_emotion('anxious')}")

    # 8. Access metadata
    print("\n8. Accessing metadata...")
    description = sarah.get_metadata("description")
    print(f"   Description: {description[:50]}...")
    print(f"   Age: {sarah.get_metadata('age')}")

    # 9. Get high/low traits
    print("\n9. Trait analysis...")
    high_traits = sarah.get_high_traits(threshold=0.7)
    print(f"   High traits (>0.7): {high_traits}")

    # 10. Export individual data
    print("\n10. Export individual...")
    data = sarah.to_dict()
    print(f"   Keys: {list(data.keys())}")

    print("\n" + "=" * 60)
    print("✅ Example 01 completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
