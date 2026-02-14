#!/usr/bin/env python3
"""Example 03: Traits System

This example demonstrates the 17-trait personality system in Personaut PDK,
based on the 16PF psychological model.
"""

from personaut.traits import (
    # Main class
    TraitProfile,
    # All 17 traits
    ALL_TRAITS,
    # Trait clusters
    INTERPERSONAL_TRAITS,
    COGNITIVE_TRAITS,
    EMOTIONAL_TRAITS,
    BEHAVIORAL_TRAITS,
    # Common trait constants
    WARMTH,
    DOMINANCE,
    LIVELINESS,
    EMOTIONAL_STABILITY,
    SENSITIVITY,
    # Utility functions
    get_trait_metadata,
    get_trait_cluster,
    is_valid_trait,
    # Coefficients
    get_affected_emotions,
)


def main() -> None:
    print("=" * 60)
    print("Example 03: Traits System (16PF Model)")
    print("=" * 60)

    # 1. The 17 personality traits
    print("\n1. The 17 Personality Traits:")
    print(f"   Total traits: {len(ALL_TRAITS)}")
    for trait in list(ALL_TRAITS)[:6]:
        print(f"   - {trait}")
    print("   ...")

    # 2. Trait clusters
    print("\n2. Trait Clusters:")
    print(f"   Interpersonal: {list(INTERPERSONAL_TRAITS)[:3]}...")
    print(f"   Cognitive: {list(COGNITIVE_TRAITS)[:3]}...")
    print(f"   Emotional: {list(EMOTIONAL_TRAITS)[:3]}...")
    print(f"   Behavioral: {list(BEHAVIORAL_TRAITS)[:3]}...")

    # 3. Create a trait profile
    print("\n3. Creating TraitProfile:")
    profile = TraitProfile()
    print(f"   Initial profile created")

    # 4. Set traits
    print("\n4. Setting Traits:")
    profile.set_trait(WARMTH, 0.9)
    profile.set_trait(DOMINANCE, 0.3)
    profile.set_trait(LIVELINESS, 0.7)
    profile.set_trait(EMOTIONAL_STABILITY, 0.5)
    profile.set_trait(SENSITIVITY, 0.8)
    print(f"   Warmth: {profile.get_trait(WARMTH)}")
    print(f"   Dominance: {profile.get_trait(DOMINANCE)}")
    print(f"   Liveliness: {profile.get_trait(LIVELINESS)}")

    # 5. Get high and low traits
    print("\n5. Trait Analysis:")
    high = profile.get_high_traits(threshold=0.7)
    low = profile.get_low_traits(threshold=0.4)
    print(f"   High traits (>0.7): {high}")
    print(f"   Low traits (<0.4): {low}")

    # 6. Trait metadata
    print("\n6. Trait Metadata:")
    print(f"   Trait: {WARMTH}")
    print(f"   Cluster: {get_trait_cluster(WARMTH)}")

    # 7. Validate traits
    print("\n7. Trait Validation:")
    print(f"   'warmth' is valid: {is_valid_trait('warmth')}")
    print(f"   'friendliness' is valid: {is_valid_trait('friendliness')}")
    print(f"   DOMINANCE is valid: {is_valid_trait(DOMINANCE)}")

    # 8. Trait-emotion coefficients
    print("\n8. Trait-Emotion Coefficients:")
    print("   Traits affect how emotions are expressed.")
    affected = get_affected_emotions(WARMTH)
    print(f"   Emotions affected by {WARMTH}: {list(affected)[:4]}...")

    # 9. Export profile
    print("\n9. Export Profile:")
    exported = profile.to_dict()
    non_default = {k: v for k, v in exported.items() if v != 0.5}
    print(f"   Non-default traits: {non_default}")

    print("\n" + "=" * 60)
    print("✅ Example 03 completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
