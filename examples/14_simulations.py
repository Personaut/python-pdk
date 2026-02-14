#!/usr/bin/env python3
"""Example 14: Simulations

This example demonstrates the **Simulations** system in Personaut PDK.

Simulations orchestrate interactions between individuals based on their
emotional states, personality traits, and situational context.

Simulation types:
    • CONVERSATION     — multi-turn dialogue between individuals
    • SURVEY           — questionnaire responses shaped by emotion/traits
    • OUTCOME_SUMMARY  — probabilistic outcome analysis with factor scoring
    • LIVE_CONVERSATION— real-time interactive chat sessions

Output styles:
    • SCRIPT           — screenplay-like dialogue
    • QUESTIONNAIRE    — structured Q&A
    • NARRATIVE         — prose analysis
    • JSON             — machine-readable format
    • TXT              — plain text
"""

import tempfile
from pathlib import Path

# ── PDK imports ────────────────────────────────────────────────────────────
import personaut
from personaut.simulations import (
    CONVERSATION,
    LIVE_CONVERSATION,
    OUTCOME_SUMMARY,
    SURVEY,
    ChatMessage,
    ChatSession,
    ConversationSimulation,
    LiveSimulation,
    OutcomeSimulation,
    Simulation,
    SimulationResult,
    SimulationStyle,
    SimulationType,
    SurveySimulation,
    create_simulation,
    parse_simulation_style,
    parse_simulation_type,
    QUESTION_TYPES,
)
from personaut.situations import create_situation
from personaut.types import Modality


def main() -> None:
    print("=" * 60)
    print("Example 14: Simulations")
    print("=" * 60)

    # ── 1. Simulation types & styles ──────────────────────────────────
    print("\n1. Simulation types:")
    for sim_type in SimulationType:
        print(f"   • {sim_type.value:<20} — {sim_type.description}")
        print(f"     interactive={sim_type.is_interactive}  "
              f"multi-turn={sim_type.supports_multi_turn}  "
              f"default_style={sim_type.default_style}")

    print("\n   Output styles:")
    for style in SimulationStyle:
        print(f"   • {style.value:<15} — {style.description}  "
              f"(ext={style.extension}, structured={style.is_structured})")

    # ── 2. Parsing helpers ────────────────────────────────────────────
    print("\n2. Parsing from strings:")
    for name in ["conversation", "survey", "outcome_summary"]:
        parsed = parse_simulation_type(name)
        print(f"   '{name}' → {parsed}")
    for name in ["script", "json", "narrative"]:
        parsed = parse_simulation_style(name)
        print(f"   '{name}' → {parsed}")

    # ── 3. Set up individuals and situation ───────────────────────────
    print("\n3. Setting up individuals and situation:")
    sarah = personaut.create_individual(
        name="Sarah",
        age=28,
        traits={"warmth": 0.9, "liveliness": 0.8, "openness": 0.7},
        emotional_state={"cheerful": 0.7, "hopeful": 0.5},
        metadata={"occupation": "barista"},
    )
    mike = personaut.create_individual(
        name="Mike",
        age=32,
        traits={"reasoning": 0.9, "social_boldness": 0.6, "warmth": 0.5},
        emotional_state={"content": 0.6, "thoughtful": 0.4},
        metadata={"occupation": "architect"},
    )
    print(f"   Sarah: cheerful={sarah.emotional_state.get_emotion('cheerful'):.1f}")
    print(f"   Mike:  content={mike.emotional_state.get_emotion('content'):.1f}")

    situation = create_situation(
        modality=Modality.IN_PERSON,
        description="Morning coffee at a friendly neighborhood cafe",
        location="Sunrise Cafe, Miami FL",
        participants=["sarah", "mike"],
    )
    print(f"   Situation: {situation.description}")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # ── 4. Conversation simulation ────────────────────────────────
        print("\n4. Conversation simulation:")

        conv = create_simulation(
            situation=situation,
            individuals=[sarah, mike],
            type=SimulationType.CONVERSATION,
            style=SimulationStyle.SCRIPT,
        )
        print(f"   Type: {type(conv).__name__}")

        results = conv.run(num=1, dir=str(output_dir / "conversations"))
        result = results[0]
        print(f"   Simulation ID: {result.simulation_id}")
        print(f"   Output path: {result.output_path.name if result.output_path else 'N/A'}")
        print(f"   Content preview:")
        for line in result.content.split("\n")[:6]:
            if line.strip():
                print(f"      {line}")

        # ── 5. Conversation with custom turn count ────────────────────
        print("\n5. Custom conversation (3 turns):")
        conv_short = ConversationSimulation(
            situation=situation,
            individuals=[sarah, mike],
            simulation_type=SimulationType.CONVERSATION,
            max_turns=3,
            include_actions=True,
        )
        results_short = conv_short.run(num=1, dir=str(output_dir / "short"))
        for line in results_short[0].content.split("\n"):
            if line.strip():
                print(f"      {line}")

        # ── 6. Survey simulation ──────────────────────────────────────
        print("\n6. Survey simulation:")
        print(f"   Question types: {list(QUESTION_TYPES.keys())}")

        questions = [
            {
                "id": "q1",
                "text": "How satisfied are you with your current work-life balance?",
                "type": "likert_5",
            },
            {
                "id": "q2",
                "text": "Do you feel supported by your colleagues?",
                "type": "yes_no",
            },
            {
                "id": "q3",
                "text": "What is your preferred communication style?",
                "type": "multiple_choice",
                "options": ["Email", "Chat", "In-person", "Video call"],
            },
            {
                "id": "q4",
                "text": "Describe your ideal work environment.",
                "type": "open_ended",
            },
        ]

        survey = create_simulation(
            situation=situation,
            individuals=[sarah],
            type=SimulationType.SURVEY,
            questions=questions,
        )
        survey_results = survey.run(num=1, dir=str(output_dir / "surveys"))

        print(f"   Survey output:")
        for line in survey_results[0].content.split("\n")[:12]:
            print(f"      {line}")

        # ── 7. Outcome simulation ─────────────────────────────────────
        print("\n7. Outcome simulation:")
        outcome = create_simulation(
            situation=situation,
            individuals=[sarah, mike],
            type=SimulationType.OUTCOME_SUMMARY,
            target_outcome="Sarah and Mike become regular coffee buddies",
        )
        outcome_results = outcome.run(num=1, dir=str(output_dir / "outcomes"))
        print(f"   Output preview:")
        for line in outcome_results[0].content.split("\n")[:10]:
            if line.strip():
                print(f"      {line}")

        # ── 8. Batch outcome with randomization ───────────────────────
        print("\n8. Batch outcome analysis (5 runs):")
        batch_outcome = OutcomeSimulation(
            situation=situation,
            individuals=[sarah, mike],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            target_outcome="Sarah convinces Mike to try her new latte recipe",
            randomize_emotions=["cheerful", "creative", "anxious"],
            randomize_range=(0.2, 0.8),
        )
        batch_results = batch_outcome.run(num=5, dir=str(output_dir / "batch"))

        # Read aggregate summary
        summary_path = output_dir / "batch" / "outcome_summary.txt"
        if summary_path.exists():
            print(f"   Aggregate summary:")
            for line in summary_path.read_text().split("\n"):
                print(f"      {line}")

        # ── 9. SimulationResult inspection ────────────────────────────
        print("\n9. SimulationResult inspection:")
        r = batch_results[0]
        print(f"   ID: {r.simulation_id}")
        print(f"   Type: {r.simulation_type.value}")
        print(f"   Created at: {r.created_at.isoformat()[:19]}")
        r_dict = r.to_dict()
        print(f"   to_dict keys: {list(r_dict.keys())}")
        r_json = r.to_json()
        print(f"   to_json length: {len(r_json)} chars")

        # ── 10. Live simulation (chat sessions) ───────────────────────
        print("\n10. Live simulation (programmatic chat):")
        human = personaut.create_individual(
            name="User",
            age=25,
            metadata={"is_human": True},
        )
        live = LiveSimulation(
            situation=situation,
            individuals=[sarah, human],
            simulation_type=SimulationType.LIVE_CONVERSATION,
            show_emotions=True,
            show_triggers=True,
        )

        # Create a chat session
        chat = live.create_chat_session()
        print(f"   Session ID: {chat.session_id}")

        # Send messages
        response1 = chat.send("Hey Sarah! What's your favorite drink here?")
        print(f"   User: Hey Sarah! What's your favorite drink here?")
        print(f"   {response1.sender}: {response1.content}")

        response2 = chat.send("That sounds great, I'll try it!")
        print(f"   User: That sounds great, I'll try it!")
        print(f"   {response2.sender}: {response2.content}")

        # ── 11. Chat session state ────────────────────────────────────
        print("\n11. Chat session state:")
        state = chat.get_state()
        print(f"   Active: {state['active']}")
        print(f"   Messages: {state['message_count']}")
        print(f"   Dominant emotion: {state['dominant_emotion']}")
        print(f"   Duration: {state['duration']:.1f}s")

        # ── 12. Chat history ──────────────────────────────────────────
        print("\n12. Chat history:")
        history = chat.get_history()
        for msg in history:
            sender = msg["sender"]
            content = msg["content"][:60]
            print(f"   [{sender}] {content}")

        # ── 13. Save/load session ─────────────────────────────────────
        print("\n13. Save & load session:")
        session_path = output_dir / "chat_session.json"
        live.save_session(chat, session_path)
        print(f"   Saved to: {session_path.name} ({session_path.stat().st_size:,} bytes)")

        loaded = live.load_session(session_path)
        print(f"   Loaded session: {loaded.session_id}")
        print(f"   Messages restored: {len(loaded.messages)}")

        # End the session
        chat.end()
        print(f"   Session ended: active={chat.get_state()['active']}")

        # ── 14. Factory function convenience ──────────────────────────
        print("\n14. Factory function (create_simulation):")
        for sim_type in ["conversation", "survey", "outcome_summary"]:
            sim = create_simulation(
                situation=situation,
                individuals=[sarah, mike],
                type=sim_type,
                **({"questions": questions} if sim_type == "survey" else {}),
                **({"target_outcome": "Test"} if sim_type == "outcome_summary" else {}),
            )
            print(f"   '{sim_type}' → {type(sim).__name__}")

        # ── 15. JSON output style ─────────────────────────────────────
        print("\n15. JSON output style:")
        json_conv = create_simulation(
            situation=situation,
            individuals=[sarah, mike],
            type=SimulationType.CONVERSATION,
            style=SimulationStyle.JSON,
        )
        json_results = json_conv.run(num=1, dir=str(output_dir / "json_out"))
        print(f"   JSON output preview:")
        for line in json_results[0].content.split("\n")[:8]:
            print(f"      {line}")

        # ── 16. Multiple output files ─────────────────────────────────
        print("\n16. Batch generation files:")
        batch_conv = create_simulation(
            situation=situation,
            individuals=[sarah, mike],
            type=SimulationType.CONVERSATION,
        )
        batch_conv_results = batch_conv.run(num=3, dir=str(output_dir / "batch_conv"))
        batch_dir = output_dir / "batch_conv"
        files = sorted(batch_dir.glob("*"))
        print(f"   Generated {len(files)} files in {batch_dir.name}/:")
        for f in files[:3]:
            print(f"   • {f.name}  ({f.stat().st_size:,} bytes)")

    print("\n" + "=" * 60)
    print("✅ Example 14 completed successfully!")
    print("=" * 60)
    print("\nKey Insight: Simulations are the orchestration layer —")
    print("they combine individuals, situations, and context to")
    print("produce conversations, surveys, and outcome analyses.")
    print("The factory function handles subclass selection automatically.")


if __name__ == "__main__":
    main()
