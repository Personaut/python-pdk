"""Conversation simulation for Personaut PDK.

This module provides the ConversationSimulation class for generating
multi-turn dialogues between individuals.

Example:
    >>> from personaut.simulations.conversation import ConversationSimulation
    >>> simulation = ConversationSimulation(
    ...     situation=coffee_shop,
    ...     individuals=[sarah, mike],
    ...     simulation_type=SimulationType.CONVERSATION,
    ... )
    >>> results = simulation.run(num=5, dir="./")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from personaut.simulations.simulation import Simulation
from personaut.simulations.styles import SimulationStyle


logger = logging.getLogger(__name__)


@dataclass
class ConversationSimulation(Simulation):
    """Simulation for multi-turn conversations between individuals.

    Generates realistic dialogues based on each participant's emotional
    state, personality traits, and the situational context.

    Attributes:
        max_turns: Maximum number of conversation turns.
        turn_order: How to determine speaker order ('sequential', 'dynamic').
        include_actions: Whether to include physical actions/gestures.
        update_emotions: Whether to update emotional states during conversation.
        create_memories: Whether to create memories from the interaction.

    Example:
        >>> simulation = ConversationSimulation(
        ...     situation=situation,
        ...     individuals=[sarah, mike],
        ...     simulation_type=SimulationType.CONVERSATION,
        ...     max_turns=10,
        ... )
    """

    max_turns: int = 10
    turn_order: str = "sequential"
    include_actions: bool = True
    update_emotions: bool = True
    create_memories: bool = True

    # Internal state
    _prompt_manager: Any = field(default=None, repr=False)
    _conversation_history: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def _generate(self, run_index: int = 0, **options: Any) -> str:
        """Generate a multi-turn conversation.

        Args:
            run_index: Index of this run (0-based).
            **options: Additional options like max_turns, turn_order.

        Returns:
            Formatted conversation content.
        """
        # Override defaults with options
        max_turns = options.get("max_turns", self.max_turns)
        include_actions = options.get("include_actions", self.include_actions)

        # Reset conversation history for this run
        self._conversation_history = []

        # Generate turns
        turns = []
        current_speaker_idx = 0

        for turn_num in range(max_turns):
            speaker = self.individuals[current_speaker_idx]
            speaker_name = self._get_individual_name(speaker)

            # Generate response for this speaker
            response = self._generate_turn(
                speaker=speaker,
                turn_number=turn_num,
                include_actions=include_actions,
            )

            # Record turn
            turn_data = {
                "speaker": speaker_name,
                "content": response,
                "turn": turn_num,
            }
            self._conversation_history.append(turn_data)
            turns.append(turn_data)

            # Update speaker for next turn
            if self.turn_order == "sequential":
                current_speaker_idx = (current_speaker_idx + 1) % len(self.individuals)
            else:
                # Dynamic turn order - for now just alternate
                current_speaker_idx = (current_speaker_idx + 1) % len(self.individuals)

        # Format output
        return self._format_conversation(turns)

    def _generate_turn(
        self,
        speaker: Any,
        turn_number: int,
        include_actions: bool = True,
    ) -> str:
        """Generate a single conversation turn.

        Args:
            speaker: The individual speaking.
            turn_number: Current turn number.
            include_actions: Whether to include actions.

        Returns:
            Generated response text.
        """
        # Get speaker info
        speaker_name = self._get_individual_name(speaker)
        emotional_state = self._get_emotional_state(speaker)
        traits = self._get_traits(speaker)

        # Build context from conversation history
        history_context = self._build_history_context()

        # If an LLM is available, use it for real generation
        if self.llm is not None:
            return self._generate_llm_turn(
                speaker=speaker,
                speaker_name=speaker_name,
                emotional_state=emotional_state,
                traits=traits,
                history_context=history_context,
                turn_number=turn_number,
                include_actions=include_actions,
            )

        # No LLM configured — warn once and fall back to placeholder
        if turn_number == 0:
            logger.warning(
                "No LLM configured for simulation. "
                "Pass llm=, provider=, or model= to create_simulation() "
                "for persona-driven dialogue. Falling back to placeholder responses."
            )
            # Opening line
            response = self._generate_opening(speaker_name, emotional_state, include_actions)
        else:
            # Continuation
            response = self._generate_continuation(speaker_name, emotional_state, history_context, include_actions)

        return response

    def _generate_llm_turn(
        self,
        speaker: Any,
        speaker_name: str,
        emotional_state: Any,
        traits: Any,
        history_context: str,
        turn_number: int,
        include_actions: bool = True,
    ) -> str:
        """Generate a conversation turn using the LLM.

        Uses PromptManager to build a rich persona prompt incorporating
        the speaker's traits, emotions, relationships, and memories,
        then sends it to the configured LLM.

        Args:
            speaker: The speaking individual.
            speaker_name: Name of the speaker.
            emotional_state: Speaker's emotional state.
            traits: Speaker's trait profile.
            history_context: Summary of conversation so far.
            turn_number: Current turn number.
            include_actions: Whether to include actions.

        Returns:
            LLM-generated response text.
        """
        from personaut.prompts.manager import PromptManager

        # Lazily initialize the prompt manager
        if self._prompt_manager is None:
            self._prompt_manager = PromptManager(default_template="conversation")

        # Build other_participants list (everyone except the speaker)
        other_participants = [ind for ind in self.individuals if ind is not speaker]

        # Get speaker memories if available
        memories = None
        if hasattr(speaker, "get_memories"):
            memories = speaker.get_memories(limit=5)

        # Generate the rich persona prompt via PromptManager
        persona_prompt = self._prompt_manager.generate(
            individual=speaker,
            situation=self.situation,
            other_participants=other_participants,
            relationships=self.relationships if self.relationships else None,
            memories=memories,
            template="conversation",
        )

        # Build the final prompt: persona context + conversation history + instruction
        prompt_parts = [persona_prompt]

        if history_context:
            prompt_parts.append(f"\nConversation so far:\n{history_context}")

        # Instruction
        if include_actions:
            prompt_parts.append(
                f"\nGenerate the next line of dialogue for {speaker_name}. "
                "Include brief physical actions or gestures in parentheses where "
                "natural, e.g. '(smiles) Hello!'. Keep the response to 1-3 sentences. "
                "Respond with ONLY the dialogue line, no speaker label."
            )
        else:
            prompt_parts.append(
                f"\nGenerate the next line of dialogue for {speaker_name}. "
                "Keep the response to 1-3 sentences. "
                "Respond with ONLY the dialogue line, no speaker label."
            )

        prompt = "\n".join(prompt_parts)

        try:
            assert self.llm is not None  # Caller gates on self.llm
            result = self.llm.generate(prompt, temperature=0.8, max_tokens=256)
            return result.text.strip()  # type: ignore[no-any-return]
        except Exception as exc:
            logger.warning("LLM generation failed for %s, falling back to placeholder: %s", speaker_name, exc)
            # Fall back to placeholder on error
            if turn_number == 0:
                return self._generate_opening(speaker_name, emotional_state, include_actions)
            return self._generate_continuation(speaker_name, emotional_state, history_context, include_actions)

    def _generate_opening(
        self,
        speaker_name: str,
        emotional_state: Any,
        include_actions: bool,
    ) -> str:
        """Generate an opening line.

        Args:
            speaker_name: Name of the speaker.
            emotional_state: Speaker's emotional state.
            include_actions: Whether to include actions.

        Returns:
            Opening line text.
        """
        # Get dominant emotion for flavor
        dominant = self._get_dominant_emotion(emotional_state)

        action = ""
        if include_actions:
            if dominant in ("anxious", "insecure", "helpless"):
                action = "(shifts nervously) "
            elif dominant in ("proud", "excited", "energetic"):
                action = "(smiles warmly) "
            elif dominant in ("cheerful", "trusting", "loving"):
                action = "(approaches with a friendly wave) "
            else:
                action = ""

        # Generate based on situation
        getattr(self.situation, "description", "meeting")

        return f"{action}Hi, I don't think we've met. I'm {speaker_name}."

    def _generate_continuation(
        self,
        speaker_name: str,
        emotional_state: Any,
        history_context: str,
        include_actions: bool,
    ) -> str:
        """Generate a continuation line.

        Args:
            speaker_name: Name of the speaker.
            emotional_state: Speaker's emotional state.
            history_context: Summary of conversation so far.
            include_actions: Whether to include actions.

        Returns:
            Continuation line text.
        """
        # Get the last speaker's message to respond to
        last_turn = self._conversation_history[-1] if self._conversation_history else {}
        last_turn.get("speaker", "")
        last_turn.get("content", "")

        # Simple response generation
        action = ""
        if include_actions:
            dominant = self._get_dominant_emotion(emotional_state)
            if dominant in ("thoughtful", "creative"):
                action = "(leans in with interest) "
            elif dominant in ("anxious", "insecure"):
                action = "(nods thoughtfully) "
            else:
                action = ""

        return f"{action}That's interesting. Tell me more about that."

    def _build_history_context(self) -> str:
        """Build a context string from conversation history.

        Returns:
            Summary of conversation history.
        """
        if not self._conversation_history:
            return ""

        lines = []
        for turn in self._conversation_history[-5:]:  # Last 5 turns
            speaker = turn.get("speaker", "Unknown")
            content = turn.get("content", "")
            lines.append(f"{speaker}: {content}")

        return "\n".join(lines)

    def _get_dominant_emotion(self, emotional_state: Any) -> str:
        """Get the dominant emotion from an emotional state.

        Args:
            emotional_state: Emotional state object.

        Returns:
            Name of the dominant emotion.
        """
        if emotional_state is None:
            return "neutral"

        if hasattr(emotional_state, "get_dominant"):
            dominant = emotional_state.get_dominant()
            return dominant[0] if dominant else "neutral"

        if isinstance(emotional_state, dict):
            if not emotional_state:
                return "neutral"
            result = max(emotional_state.items(), key=lambda x: x[1])[0]
            return str(result)

        return "neutral"

    def _format_conversation(self, turns: list[dict[str, Any]]) -> str:
        """Format conversation turns into output.

        Args:
            turns: List of turn dictionaries.

        Returns:
            Formatted conversation string.
        """
        if self.style == SimulationStyle.JSON:
            return self._format_json(turns)
        else:
            return self._format_script(turns)

    def _format_script(self, turns: list[dict[str, Any]]) -> str:
        """Format as screenplay-style script.

        Args:
            turns: List of turn dictionaries.

        Returns:
            Script-formatted string.
        """
        # Header
        situation_desc = getattr(self.situation, "description", "Conversation")
        location = getattr(self.situation, "location", None)
        participants = [self._get_individual_name(ind) for ind in self.individuals]

        lines = [
            "=== Conversation Simulation ===",
            f"Situation: {situation_desc}",
        ]
        if location:
            lines.append(f"Location: {location}")
        lines.append(f"Participants: {', '.join(participants)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Turns
        for turn in turns:
            speaker = turn["speaker"].upper()
            content = turn["content"]
            lines.append(f"{speaker}: {content}")
            lines.append("")

        return "\n".join(lines)

    def _format_json(self, turns: list[dict[str, Any]]) -> str:
        """Format as JSON.

        Args:
            turns: List of turn dictionaries.

        Returns:
            JSON-formatted string.
        """
        import json

        output = {
            "simulation_type": "conversation",
            "situation": {
                "description": getattr(self.situation, "description", ""),
                "location": getattr(self.situation, "location", None),
            },
            "participants": [self._get_individual_name(ind) for ind in self.individuals],
            "turns": [
                {
                    "turn": turn.get("turn", i),
                    "speaker": turn["speaker"],
                    "content": turn["content"],
                }
                for i, turn in enumerate(turns)
            ],
        }
        return json.dumps(output, indent=2)


__all__ = ["ConversationSimulation"]
