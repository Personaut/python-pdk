#!/usr/bin/env python3
"""Example 12: State Calculation & Markov Transitions

This example demonstrates the **States** system in Personaut PDK.

The states module provides tools for calculating and transitioning
between emotional states:
    • StateCalculator — computes aggregate states from history snapshots
    • StateMode       — AVERAGE, MAXIMUM, MINIMUM, RECENT, CUSTOM
    • MarkovTransitionMatrix — probabilistic state transitions between
      emotion categories (joy → sadness, fear → peaceful, etc.)
"""

# ── PDK imports ────────────────────────────────────────────────────────────
from personaut.emotions import EmotionCategory, EmotionalState
from personaut.states import (
    AVERAGE,
    MAXIMUM,
    MINIMUM,
    RECENT,
    MarkovTransitionMatrix,
    StateCalculator,
    StateMode,
    parse_state_mode,
)


def main() -> None:
    print("=" * 60)
    print("Example 12: State Calculation & Markov Transitions")
    print("=" * 60)

    # ── 1. State calculation modes ────────────────────────────────────
    print("\n1. State calculation modes:")
    for mode in StateMode:
        print(f"   • {mode.value}")

    # ── 2. Parse mode from string ─────────────────────────────────────
    print("\n2. Parsing mode from string:")
    for name in ["average", "MAXIMUM", "Recent", "minimum"]:
        mode = parse_state_mode(name)
        print(f"   '{name}' → {mode.value}")

    # ── 3. Create state snapshots (a history) ─────────────────────────
    print("\n3. State history snapshots:")
    states = []

    # Snapshot 1: Sarah arrives cheerful
    s1 = EmotionalState()
    s1.change_emotion("cheerful", 0.8)
    s1.change_emotion("hopeful", 0.5)
    states.append(s1)
    print(f"   T=1: cheerful=0.8, hopeful=0.5")

    # Snapshot 2: Gets stressed mid-day
    s2 = EmotionalState()
    s2.change_emotion("cheerful", 0.3)
    s2.change_emotion("anxious", 0.6)
    s2.change_emotion("hopeful", 0.2)
    states.append(s2)
    print(f"   T=2: cheerful=0.3, anxious=0.6, hopeful=0.2")

    # Snapshot 3: Recovers by evening
    s3 = EmotionalState()
    s3.change_emotion("cheerful", 0.5)
    s3.change_emotion("content", 0.7)
    s3.change_emotion("hopeful", 0.6)
    states.append(s3)
    print(f"   T=3: cheerful=0.5, content=0.7, hopeful=0.6")

    # ── 4. AVERAGE calculation ────────────────────────────────────────
    print("\n4. AVERAGE mode (mean across snapshots):")
    calc = StateCalculator(mode=StateMode.AVERAGE)
    for state in states:
        calc.add_state(state)
    avg = calc.get_calculated_state()
    print(f"   cheerful: {avg.get_emotion('cheerful'):.2f}  (avg of 0.8, 0.3, 0.5)")
    print(f"   hopeful:  {avg.get_emotion('hopeful'):.2f}  (avg of 0.5, 0.2, 0.6)")
    print(f"   anxious:  {avg.get_emotion('anxious'):.2f}  (avg of 0.0, 0.6, 0.0)")

    # ── 5. MAXIMUM calculation ────────────────────────────────────────
    print("\n5. MAXIMUM mode (peak of each emotion):")
    calc_max = StateCalculator(mode=StateMode.MAXIMUM)
    for state in states:
        calc_max.add_state(state)
    peak = calc_max.get_calculated_state()
    print(f"   cheerful: {peak.get_emotion('cheerful'):.2f}  (max of 0.8, 0.3, 0.5)")
    print(f"   anxious:  {peak.get_emotion('anxious'):.2f}  (max of 0.0, 0.6, 0.0)")

    # ── 6. MINIMUM calculation ────────────────────────────────────────
    print("\n6. MINIMUM mode (floor of each emotion):")
    calc_min = StateCalculator(mode=StateMode.MINIMUM)
    for state in states:
        calc_min.add_state(state)
    floor = calc_min.get_calculated_state()
    print(f"   cheerful: {floor.get_emotion('cheerful'):.2f}  (min of 0.8, 0.3, 0.5)")
    print(f"   hopeful:  {floor.get_emotion('hopeful'):.2f}  (min of 0.5, 0.2, 0.6)")

    # ── 7. RECENT mode (last snapshot wins) ───────────────────────────
    print("\n7. RECENT mode (last snapshot):")
    calc_recent = StateCalculator(mode=StateMode.RECENT)
    for state in states:
        calc_recent.add_state(state)
    recent = calc_recent.get_calculated_state()
    print(f"   cheerful: {recent.get_emotion('cheerful'):.2f}  (T=3 value)")
    print(f"   content:  {recent.get_emotion('content'):.2f}  (T=3 value)")
    print(f"   anxious:  {recent.get_emotion('anxious'):.2f}  (T=3 value)")

    # ── 8. Custom calculator ──────────────────────────────────────────
    print("\n8. CUSTOM mode (user defined):")

    def weighted_recent(history: list[EmotionalState]) -> EmotionalState:
        """Weight recent states more heavily using exponential decay."""
        if not history:
            return EmotionalState()

        # Collect all emotions across all states
        all_emotions: dict[str, float] = {}
        weights: list[float] = []
        total_weight = 0.0

        for i, state in enumerate(history):
            w = 2.0 ** i  # Exponentially more weight to recent
            weights.append(w)
            total_weight += w

        for emotion_name in {e for s in history for e, v in s.to_dict().items() if v > 0}:
            weighted_sum = sum(
                s.get_emotion(emotion_name) * weights[i]
                for i, s in enumerate(history)
            )
            all_emotions[emotion_name] = min(weighted_sum / total_weight, 1.0)

        result = EmotionalState()
        for emotion_name, value in all_emotions.items():
            result.change_emotion(emotion_name, value)
        return result

    calc_custom = StateCalculator(mode=StateMode.CUSTOM, custom_function=weighted_recent)
    for state in states:
        calc_custom.add_state(state)
    custom = calc_custom.get_calculated_state()
    print(f"   cheerful: {custom.get_emotion('cheerful'):.2f}  (weighted toward T=3)")
    print(f"   content:  {custom.get_emotion('content'):.2f}  (weighted toward T=3)")

    # ── 9. History management ─────────────────────────────────────────
    print("\n9. History management:")
    print(f"   History size: {len(calc.get_history())}")
    calc.clear_history()
    print(f"   After clear: {len(calc.get_history())}")

    # ── 10. Markov transition matrix ──────────────────────────────────
    print("\n10. Markov transition matrix:")
    markov = MarkovTransitionMatrix()
    print(f"   Volatility: {markov.volatility}")
    print(f"   Emotion categories: {[c.value for c in EmotionCategory]}")

    # Show some transition probabilities
    print("\n   Transition probabilities:")
    for from_cat in [EmotionCategory.JOY, EmotionCategory.FEAR, EmotionCategory.SAD]:
        probs = []
        for to_cat in EmotionCategory:
            p = markov.get_transition_probability(from_cat, to_cat)
            if p > 0:
                probs.append(f"{to_cat.value}={p:.2f}")
        print(f"   {from_cat.value:>10} → {', '.join(probs[:4])}")

    # ── 11. Simulate state transitions ────────────────────────────────
    print("\n11. Simulated state transitions:")
    current_state = EmotionalState()
    current_state.change_emotion("cheerful", 0.8)
    current_state.change_emotion("excited", 0.5)

    dominant = current_state.get_dominant()
    dom_name = dominant[0] if dominant else "neutral"
    print(f"   Start: {dom_name} ({dominant[1]:.2f})" if dominant else "   Start: neutral")

    for step in range(1, 4):
        next_state = markov.next_state(current_state)
        dominant = next_state.get_dominant()
        if dominant:
            dom_name, dom_val = dominant
            print(f"   Step {step}: dominant = {dom_name} ({dom_val:.2f})")
        current_state = next_state

    # ── 12. Volatility comparison ─────────────────────────────────────
    print("\n12. Volatility comparison:")
    low_vol = MarkovTransitionMatrix(volatility=0.1)
    high_vol = MarkovTransitionMatrix(volatility=0.9)
    print(f"   Low volatility:  {low_vol.volatility} (small emotional swings)")
    print(f"   High volatility: {high_vol.volatility} (large emotional swings)")

    print("\n" + "=" * 60)
    print("✅ Example 12 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: State calculators aggregate emotional history,")
    print("while Markov transitions model how emotions naturally shift")
    print("over time — creating realistic emotional dynamics.")


if __name__ == "__main__":
    main()
