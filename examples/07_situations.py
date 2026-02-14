#!/usr/bin/env python3
"""Example 07: Situations & Context

This example demonstrates how to create and configure situations in
Personaut PDK.  A **Situation** defines the physical and social context
for an interaction — modality (in-person, text, video call, etc.),
location, time, and rich structured context.

Key concepts:
    • create_situation() — factory for quick situation creation
    • Modality enum       — IN_PERSON, TEXT_MESSAGE, PHONE_CALL, etc.
    • SituationContext    — structured, validatable context metadata
    • Context helpers     — create_environment_context, create_social_context
"""

from datetime import datetime

# ── PDK imports ────────────────────────────────────────────────────────────
from personaut.situations import (
    Situation,
    SituationContext,
    create_context,
    create_environment_context,
    create_situation,
    create_social_context,
)
from personaut.types import Modality


def main() -> None:
    print("=" * 60)
    print("Example 07: Situations & Context")
    print("=" * 60)

    # ── 1. Create a basic situation ────────────────────────────────────
    print("\n1. Basic situation:")
    coffee_shop = create_situation(
        modality=Modality.IN_PERSON,
        description="Morning rush at a busy downtown coffee shop",
        location="Sunrise Cafe, Miami FL",
    )
    print(f"   Modality:    {coffee_shop.modality.value}")
    print(f"   Description: {coffee_shop.description}")
    print(f"   Location:    {coffee_shop.location}")

    # ── 2. All modality types ──────────────────────────────────────────
    print("\n2. Modality types:")
    modalities = [
        (Modality.IN_PERSON,    "Face-to-face with full non-verbal cues"),
        (Modality.TEXT_MESSAGE,  "Casual, async text conversation"),
        (Modality.PHONE_CALL,   "Audio-only, real-time"),
        (Modality.VIDEO_CALL,   "Visual + audio, technology-mediated"),
    ]
    for mod, desc in modalities:
        sit = create_situation(modality=mod, description=desc)
        print(f"   {mod.value:<15} → {desc}")

    # ── 3. Situation with timestamp ────────────────────────────────────
    print("\n3. Timestamped situation:")
    evening_bar = create_situation(
        modality=Modality.IN_PERSON,
        description="Quiet evening at a neighborhood bar",
        time=datetime(2026, 2, 14, 21, 30),
        location="The Rusty Anchor, Brooklyn NY",
    )
    time_str = evening_bar.time.strftime("%Y-%m-%d %H:%M") if evening_bar.time else "N/A"
    print(f"   Time:     {time_str}")
    print(f"   Location: {evening_bar.location}")

    # ── 4. Structured context with SituationContext ────────────────────
    print("\n4. Structured context:")
    ctx = SituationContext()
    ctx.set("environment.lighting", "dim, warm Edison bulbs")
    ctx.set("environment.noise_level", "moderate — background music, clinking glasses")
    ctx.set("atmosphere", "relaxed, end-of-day vibe")
    ctx.set("social.crowd_size", "about 15 people")
    ctx.set("social.formality", "casual")

    print(f"   Context keys: {list(ctx.data.keys())}")

    bar_with_context = create_situation(
        modality=Modality.IN_PERSON,
        description="Evening at a neighborhood bar",
        context=ctx.data,
    )
    print(f"   Context: {bar_with_context.context}")

    # ── 5. Environment context helper ──────────────────────────────────
    print("\n5. Environment context helper:")
    env_ctx = create_environment_context(
        lighting="bright fluorescent",
        temperature="cool",
        noise_level="quiet, keyboard clicks",
    )
    print(f"   Environment context: {env_ctx.data}")

    # ── 6. Social context helper ───────────────────────────────────────
    print("\n6. Social context helper:")
    social_ctx = create_social_context(
        formality="business casual",
        crowd_level="8 people",
    )
    print(f"   Social context: {social_ctx.data}")

    # ── 7. Combining contexts ──────────────────────────────────────────
    print("\n7. Combined context:")
    combined = {**env_ctx.data, **social_ctx.data}
    office = create_situation(
        modality=Modality.VIDEO_CALL,
        description="Weekly standup meeting",
        context=combined,
    )
    print(f"   Modality: {office.modality.value}")
    print(f"   Context keys: {list(office.context.keys()) if office.context else '(none)'}")

    # ── 8. Situation features ─────────────────────────────────────────
    print("\n8. Situation features:")
    print(f"   Is in-person:     {coffee_shop.is_in_person()}")
    print(f"   Is remote:        {coffee_shop.is_remote()}")
    print(f"   Is synchronous:   {coffee_shop.is_synchronous()}")

    video = create_situation(modality=Modality.VIDEO_CALL, description="Remote meeting")
    print(f"   Video call remote: {video.is_remote()}")

    # ── 9. Participants & tags ────────────────────────────────────────
    print("\n9. Participants and tags:")
    meeting = create_situation(
        modality=Modality.IN_PERSON,
        description="Team standup",
        participants=["sarah_001", "mike_002"],
        tags=["work", "morning"],
    )
    print(f"   Participants: {meeting.participants}")
    print(f"   Tags: {meeting.tags}")
    print(f"   Has 'sarah_001': {meeting.has_participant('sarah_001')}")
    print(f"   Has tag 'work': {meeting.has_tag('work')}")

    # ── 10. Serialization ──────────────────────────────────────────────
    print("\n10. Serialization round-trip:")
    data = coffee_shop.to_dict()
    restored = Situation.from_dict(data)
    print(f"   Original location:  {coffee_shop.location}")
    print(f"   Restored location:  {restored.location}")
    print(f"   Match: {coffee_shop.location == restored.location}")

    print("\n" + "=" * 60)
    print("✅ Example 07 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: Situations ground interactions in physical and")
    print("social reality — modality, environment, and social context all")
    print("influence how individuals communicate.")


if __name__ == "__main__":
    main()
