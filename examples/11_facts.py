#!/usr/bin/env python3
"""Example 11: Facts & Situational Context

This example demonstrates the **Facts** system in Personaut PDK.

Facts are structured, categorized pieces of situational information
(location, environment, social cues, sensory details) that ground
memories and simulations in concrete reality.

Key concepts:
    • Fact / FactCategory — atomic fact with a category, key, and value
    • SituationalContext  — aggregation of facts into a coherent scene
    • FactExtractor       — regex-based extraction from unstructured text
    • Context presets     — create_coffee_shop_context, create_office_context
"""

# ── PDK imports ────────────────────────────────────────────────────────────
from personaut.facts import (
    BEHAVIORAL_FACTS,
    ENVIRONMENT_FACTS,
    LOCATION_FACTS,
    SENSORY_FACTS,
    SOCIAL_FACTS,
    TEMPORAL_FACTS,
    ExtractionPattern,
    Fact,
    FactCategory,
    FactExtractor,
    SituationalContext,
    create_behavioral_fact,
    create_coffee_shop_context,
    create_environment_fact,
    create_location_fact,
    create_office_context,
)


def main() -> None:
    print("=" * 60)
    print("Example 11: Facts & Situational Context")
    print("=" * 60)

    # ── 1. Fact categories ────────────────────────────────────────────
    print("\n1. Fact categories:")
    for cat in FactCategory:
        print(f"   • {cat.value:<14} — {cat.description}")

    # ── 2. Fact templates per category ────────────────────────────────
    print("\n2. Built-in fact templates:")
    templates = [
        ("Location", LOCATION_FACTS),
        ("Environment", ENVIRONMENT_FACTS),
        ("Social", SOCIAL_FACTS),
        ("Sensory", SENSORY_FACTS),
        ("Temporal", TEMPORAL_FACTS),
        ("Behavioral", BEHAVIORAL_FACTS),
    ]
    for name, facts in templates:
        print(f"   {name}: {len(facts)} fact(s) — {list(facts.keys())[:3]}...")

    # ── 3. Create individual facts ────────────────────────────────────
    print("\n3. Creating facts:")
    city_fact = create_location_fact("city", "Miami, FL")
    venue_fact = create_location_fact("venue_type", "coffee shop")
    noise_fact = create_environment_fact("noise_level", "moderate chatter")
    mood_fact = create_behavioral_fact("posture", "leaning forward, engaged")

    for f in [city_fact, venue_fact, noise_fact, mood_fact]:
        print(f"   {f.category.value}/{f.key}: {f.value}")

    # ── 4. Build a SituationalContext ─────────────────────────────────
    print("\n4. SituationalContext from facts:")
    ctx = SituationalContext()
    ctx.add_fact(city_fact)
    ctx.add_fact(venue_fact)
    ctx.add_fact(noise_fact)
    ctx.add_fact(mood_fact)

    print(f"   Total facts: {len(ctx)}")
    # Get categories from facts
    categories = {f.category for f in ctx.facts}
    print(f"   Categories: {[c.value for c in categories]}")

    # ── 5. Context helper methods ─────────────────────────────────────
    print("\n5. Context helper methods:")
    ctx2 = SituationalContext(description="Morning visit")
    ctx2.add_location("city", "Portland, OR")
    ctx2.add_environment("noise_level", "quiet")
    ctx2.add_behavioral("queue_length", 3, unit="people")
    ctx2.add_temporal("time_of_day", "morning")
    ctx2.add_social("formality", "casual")
    ctx2.add_sensory("smell", "fresh coffee")

    print(f"   Total facts: {len(ctx2)}")
    print(f"   Get value: city = {ctx2.get_value('city')}")
    print(f"   Get fact: {ctx2.get_fact('queue_length')}")
    print(f"   Contains 'city'? {'city' in ctx2}")

    # ── 6. Embedding text for vector search ───────────────────────────
    print("\n6. Embedding text (for memory search):")
    embed_text = ctx2.to_embedding_text()
    for line in embed_text.strip().split("\n")[:4]:
        print(f"   {line}")

    # ── 7. Coffee shop preset ─────────────────────────────────────────
    print("\n7. Coffee shop context preset:")
    cafe = create_coffee_shop_context(
        city="Miami, FL",
        venue_name="Sunrise Cafe",
        capacity_percent=80,
        queue_length=5,
    )
    facts_by_cat: dict[str, list[str]] = {}
    for fact in cafe.facts:
        facts_by_cat.setdefault(fact.category.value, []).append(f"{fact.key}={fact.value}")
    for cat, items in facts_by_cat.items():
        print(f"   {cat}: {', '.join(items[:3])}")

    # ── 8. Office preset ──────────────────────────────────────────────
    print("\n8. Office context preset:")
    office = create_office_context(
        city="Seattle, WA",
        company_name="Acme Corp",
        floor=12,
    )
    print(f"   Facts: {len(office)}")
    for fact in office.facts[:3]:
        print(f"   • {fact.key}: {fact.value}")

    # ── 9. Regex-based fact extraction ────────────────────────────────
    print("\n9. FactExtractor (regex-based):")
    extractor = FactExtractor()

    texts = [
        "It was a rainy Tuesday afternoon at a busy cafe in Portland",
        "The quiet library was almost empty, just the sound of pages turning",
        "A crowded nightclub in downtown Las Vegas, music blaring",
    ]

    for text in texts:
        result = extractor.extract(text)
        facts_str = "; ".join(f"{f.key}={f.value}" for f in result.facts[:3])
        print(f"   '{text[:50]}...'")
        print(f"   → {len(result.facts)} fact(s): {facts_str or '(none matched)'}")

    # ── 10. Custom extraction patterns ────────────────────────────────
    print("\n10. Custom extraction patterns:")
    custom = FactExtractor([
        ExtractionPattern(
            pattern=r"(?:drinking|sipping|holding)\s+([\w\s]+)",
            category=FactCategory.BEHAVIORAL,
            key="beverage",
        ),
    ])
    result = custom.extract("She was sipping a cappuccino while reading")
    for fact in result.facts:
        print(f"   Extracted: {fact.key} = {fact.value}")

    # ── 11. Merging contexts ──────────────────────────────────────────
    print("\n11. Merging contexts:")
    merged = ctx.merge(ctx2)
    print(f"   ctx1 facts: {len(ctx)}, ctx2 facts: {len(ctx2)}")
    print(f"   merged facts: {len(merged)}")

    # ── 12. Fact serialization ────────────────────────────────────────
    print("\n12. Serialization:")
    data = city_fact.to_dict()
    restored = Fact.from_dict(data)
    print(f"   Original: {city_fact.category.value}/{city_fact.key}: {city_fact.value}")
    print(f"   Restored: {restored.category.value}/{restored.key}: {restored.value}")

    print("\n" + "=" * 60)
    print("✅ Example 11 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: Facts provide structured situational grounding —")
    print("they extract concrete details from text and organize them")
    print("into searchable contexts for memory retrieval.")


if __name__ == "__main__":
    main()
