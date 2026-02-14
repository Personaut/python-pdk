#!/usr/bin/env python3
"""Example 08: Masks & Triggers

This example demonstrates the **Mask** and **Trigger** systems in the
Personaut PDK.

Masks — contextual personas that *modify* emotional expression based on
situational context.  A "professional" mask suppresses anger while at
work; a "stoic" mask dampens reactivity in a crisis.

Triggers — conditional activators that automatically modify an
individual's emotional state or activate masks when specific conditions
are met.  Two types:
    • EmotionalTrigger  — fires when emotions cross thresholds
    • SituationalTrigger — fires when keywords appear in a situation
"""

# ── PDK imports ────────────────────────────────────────────────────────────
from personaut.emotions import EmotionalState
from personaut.masks import (
    CASUAL_MASK,
    DEFAULT_MASKS,
    GUARDED_MASK,
    PROFESSIONAL_MASK,
    STOIC_MASK,
    create_mask,
    get_mask_by_name,
)
from personaut.triggers import (
    create_emotional_trigger,
    create_situational_trigger,
)


def main() -> None:
    print("=" * 60)
    print("Example 08: Masks & Triggers")
    print("=" * 60)

    # ─────────────────────────────────────────────────────────────────
    #  PART A — MASKS
    # ─────────────────────────────────────────────────────────────────

    # ── 1. Predefined masks ───────────────────────────────────────────
    print("\n── Masks ────────────────────────────────────────────────")
    print("\n1. Predefined masks:")
    for mask in DEFAULT_MASKS:
        mods = list(mask.emotional_modifications.keys())[:3]
        print(f"   • {mask.name:<16}  triggers: {mask.trigger_situations[:2]}  mods: {mods}...")

    # ── 2. Look up a mask by name ─────────────────────────────────────
    print("\n2. Look up by name:")
    pro = get_mask_by_name("professional")
    print(f"   Found: {pro.name if pro else '(not found)'}")
    print(f"   Description: {pro.description if pro else ''}")

    # ── 3. Check if a mask should trigger ─────────────────────────────
    print("\n3. Trigger check (situation text → mask activation):")
    situations = [
        "Attending an office meeting with the VP",
        "Hanging out at a barbecue",
        "Emergency evacuation drill",
        "Meeting a stranger at a party",
    ]
    masks_to_check = [PROFESSIONAL_MASK, CASUAL_MASK, STOIC_MASK, GUARDED_MASK]
    for sit in situations:
        matches = [m.name for m in masks_to_check if m.should_trigger(sit)]
        print(f"   '{sit[:40]}...' → {matches or '(none)'}")

    # ── 4. Apply a mask to an emotional state ─────────────────────────
    print("\n4. Applying PROFESSIONAL mask:")
    state = EmotionalState()
    state.change_emotion("angry", 0.8)
    state.change_emotion("cheerful", 0.3)
    state.change_emotion("anxious", 0.5)
    print(f"   Before: angry={state.get_emotion('angry'):.1f}  "
          f"cheerful={state.get_emotion('cheerful'):.1f}  "
          f"anxious={state.get_emotion('anxious'):.1f}")

    modified = PROFESSIONAL_MASK.apply(state)
    print(f"   After:  angry={modified.get_emotion('angry'):.1f}  "
          f"cheerful={modified.get_emotion('cheerful'):.1f}  "
          f"anxious={modified.get_emotion('anxious'):.1f}")
    print("   → Anger suppressed, other emotions adjusted")

    # ── 5. Create a custom mask ───────────────────────────────────────
    print("\n5. Custom mask — 'Date Night':")
    date_mask = create_mask(
        name="date_night",
        emotional_modifications={
            "anxious": -0.2,       # Less nervous
            "cheerful": 0.3,       # More upbeat
            "self_conscious": 0.2, # A little self-aware
        },
        trigger_situations=["date", "dinner", "romantic"],
        description="Activated on dates — cheerful but slightly self-conscious",
    )
    print(f"   Name: {date_mask.name}")
    print(f"   Triggers: {date_mask.trigger_situations}")
    print(f"   'romantic dinner' → should_trigger: {date_mask.should_trigger('romantic dinner')}")

    # ── 6. Serialization ──────────────────────────────────────────────
    print("\n6. Mask serialization:")
    data = date_mask.to_dict()
    from personaut.masks.mask import Mask
    restored = Mask.from_dict(data)
    print(f"   Restored: {restored.name}, mods: {restored.emotional_modifications}")

    # ─────────────────────────────────────────────────────────────────
    #  PART B — TRIGGERS
    # ─────────────────────────────────────────────────────────────────

    print("\n── Triggers ─────────────────────────────────────────────")

    # ── 7. Emotional trigger — fires when emotion exceeds threshold ──
    print("\n7. Emotional trigger (anxiety crisis):")
    crisis_trigger = create_emotional_trigger(
        description="Anxiety crisis — activate stoic mask",
        rules=[
            {"emotion": "anxious", "threshold": 0.7, "operator": ">"},
            {"emotion": "helpless", "threshold": 0.5, "operator": ">"},
        ],
        response=STOIC_MASK,         # Apply stoic mask when fired
        match_all=False,             # ANY rule matching triggers it
    )

    # Test with a calm state
    calm = EmotionalState()
    calm.change_emotion("anxious", 0.2)
    calm.change_emotion("cheerful", 0.6)
    print(f"   Calm state (anxious=0.2): fires? {crisis_trigger.check(calm)}")

    # Test with a stressed state
    stressed = EmotionalState()
    stressed.change_emotion("anxious", 0.9)
    stressed.change_emotion("helpless", 0.3)
    print(f"   Stressed state (anxious=0.9): fires? {crisis_trigger.check(stressed)}")

    # Fire the trigger and see the effect
    result = crisis_trigger.fire(stressed)
    print(f"   After firing — anxious: {result.get_emotion('anxious'):.2f} (was 0.90)")

    # ── 8. Emotional trigger with dict response ───────────────────────
    print("\n8. Emotional trigger with direct emotion changes:")
    anger_trigger = create_emotional_trigger(
        description="Anger flash — reduce warmth, increase hostility",
        rules=[{"emotion": "angry", "threshold": 0.8, "operator": ">"}],
        response={"hostile": 0.3, "warm": -0.4},  # Dict response
        match_all=True,
    )

    furious = EmotionalState()
    furious.change_emotion("angry", 0.9)
    print(f"   Angry state (angry=0.9): fires? {anger_trigger.check(furious)}")
    result = anger_trigger.fire(furious)
    print(f"   After firing — hostile: {result.get_emotion('hostile'):.2f}")

    # ── 9. Situational trigger — fires on keywords ────────────────────
    print("\n9. Situational trigger (claustrophobia):")
    claustro = create_situational_trigger(
        description="Enclosed spaces trigger anxiety",
        keywords=["basement", "closet", "elevator", "cave", "tunnel"],
        response={"anxious": 0.4, "helpless": 0.2},
    )

    print(f"   'a sunny park': fires? {claustro.check('a sunny park')}")
    print(f"   'stuck in an elevator': fires? {claustro.check('stuck in an elevator')}")
    print(f"   'deep cave exploration': fires? {claustro.check('deep cave exploration')}")

    # Fire and see emotional change
    neutral = EmotionalState()
    neutral.change_emotion("content", 0.5)
    result = claustro.fire(neutral)
    print(f"   After claustro trigger → anxious: {result.get_emotion('anxious'):.2f}, "
          f"helpless: {result.get_emotion('helpless'):.2f}")

    # ── 10. Trigger serialization ─────────────────────────────────────
    print("\n10. Trigger serialization:")
    data = crisis_trigger.to_dict()
    print(f"    Type: {data.get('type', 'emotional')}")
    print(f"    Rules: {len(data.get('rules', []))}")
    print(f"    Response type: {data.get('response', {}).get('type', 'N/A')}")

    print("\n" + "=" * 60)
    print("✅ Example 08 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: Masks and triggers work together to create")
    print("realistic behavioral adaptation — individuals automatically")
    print("adjust their emotional expression to match the situation.")


if __name__ == "__main__":
    main()
