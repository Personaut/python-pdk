"""Conversation template for dialogue simulations.

This module provides the ConversationTemplate class for generating
prompts in dialogue-based simulations between individuals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from personaut.prompts.components.memory import MemoryComponent
from personaut.prompts.components.relationship import RelationshipComponent
from personaut.prompts.components.situation import SituationComponent
from personaut.prompts.templates.base import BaseTemplate


if TYPE_CHECKING:
    from personaut.emotions.state import EmotionalState
    from personaut.situations.situation import Situation
    from personaut.traits.profile import TraitProfile


# ── Emotion → behavioral guidelines lookup ──────────────────────────────
# Complete mapping of all 36 emotions to conversational behavior cues.
# Each entry describes how the emotion manifests in real human
# conversation — body language, speech patterns, cognitive biases,
# and interpersonal tendencies.

_EMOTION_GUIDELINES: dict[str, list[str]] = {
    # ── Anger/Mad emotions ──
    "hostile": [
        "Responses are clipped and cold — minimal warmth",
        "May interpret neutral comments as provocations",
        "Body language is closed off and confrontational",
    ],
    "hurt": [
        "Responses carry an undertone of wounded feelings",
        "May withdraw or become quieter than usual",
        "Might reference the thing that hurt, even obliquely",
    ],
    "angry": [
        "Show controlled frustration — shorter sentences, more direct",
        "May raise voice (use CAPS sparingly or exclamation marks)",
        "Less patience for small talk or pleasantries",
    ],
    "selfish": [
        "Steer conversations back to own needs and interests",
        "Show less interest in others' problems",
        "May dismiss others' concerns as less important",
    ],
    "hateful": [
        "Responses drip with contempt or disdain",
        "May refuse to engage constructively",
        "Sharp, cutting remarks that target vulnerabilities",
    ],
    "critical": [
        "Point out flaws and problems readily",
        "Offer unsolicited corrections or judgments",
        "Tone is evaluative — nothing quite meets the standard",
    ],
    # ── Sad/Sadness emotions ──
    "guilty": [
        "Over-apologize or hedge statements",
        "May bring up past mistakes or failings unprompted",
        "Seek to make amends even when not asked",
    ],
    "ashamed": [
        "Avoid eye contact (mention looking away, fidgeting)",
        "Deflect compliments and minimize achievements",
        "May try to change the subject away from self",
    ],
    "depressed": [
        "Responses are flat and low-energy — shorter, less vibrant",
        "Show little enthusiasm even for normally exciting topics",
        "May express hopelessness or 'what's the point' thinking",
    ],
    "lonely": [
        "Cling to the conversation — reluctant to let it end",
        "May overshare personal details seeking connection",
        "Express gratitude for the interaction, even subtly",
    ],
    "bored": [
        "Give shorter, less engaged responses",
        "May try to change the topic to something more interesting",
        "Responses lack enthusiasm — perfunctory rather than invested",
    ],
    "apathetic": [
        "Flat, indifferent tone — 'whatever' energy",
        "Show no strong opinion on anything",
        "Minimal effort in responses — not hostile, just disengaged",
    ],
    # ── Fear/Scared emotions ──
    "rejected": [
        "Responses have a defensive edge — protecting against further rejection",
        "May preemptively withdraw or lower expectations",
        "Hyper-aware of any sign of disinterest from the other person",
    ],
    "confused": [
        "Ask clarifying questions — genuinely puzzled",
        "Hesitate before responding, may backtrack mid-thought",
        "Express uncertainty openly — 'I'm not sure I follow'",
    ],
    "submissive": [
        "Defer to the other person's opinions and preferences",
        "Use hedging language — 'if you think so', 'whatever you prefer'",
        "Avoid asserting own needs or disagreeing",
    ],
    "insecure": [
        "Second-guess statements — add qualifiers like 'I think' or 'maybe'",
        "Seek validation — 'does that make sense?' 'is that okay?'",
        "Compare self unfavorably to others",
    ],
    "anxious": [
        "Express thoughts with some hesitation or rushing",
        "May seek reassurance or anticipate worst-case scenarios",
        "Physical tells: fidgeting, speaking faster, trailing off",
    ],
    "helpless": [
        "Express feeling stuck or out of options",
        "May ask for help more readily than usual",
        "Language conveys resignation — 'I don't know what to do'",
    ],
    # ── Joy/Happiness emotions ──
    "excited": [
        "Energy is high — speak faster, use exclamation marks naturally",
        "Jump between related topics with enthusiasm",
        "Share plans and possibilities eagerly",
    ],
    "sensual": [
        "More aware of physical sensations and environment",
        "Language is more descriptive and sensory",
        "Relaxed and pleasure-oriented in conversation",
    ],
    "energetic": [
        "Dynamic, fast-paced responses with momentum",
        "Ready to take action — suggest doing things rather than just talking",
        "Upbeat tone carries through even mundane topics",
    ],
    "cheerful": [
        "Warm and positive in tone — genuine smiles come through",
        "Find the bright side naturally, without being dismissive",
        "Laugh easily and engage generously with others' remarks",
    ],
    "creative": [
        "Make unexpected connections between ideas",
        "Suggest novel approaches or unconventional solutions",
        "Language is more playful and metaphorical",
    ],
    "hopeful": [
        "Express optimism about outcomes, but grounded not naive",
        "Focus on possibilities and forward-looking plans",
        "Encouraging toward others' endeavors",
    ],
    # ── Powerful/Confident emotions ──
    "proud": [
        "Stand behind statements with conviction",
        "May reference recent accomplishments naturally",
        "Generous with praise — secure enough to lift others up",
    ],
    "respected": [
        "Carry self with quiet assurance and dignity",
        "Speak from authority without being overbearing",
        "Comfortable setting boundaries",
    ],
    "appreciated": [
        "Express genuine warmth toward the person who values them",
        "More giving and helpful — reciprocating the feeling",
        "Relaxed and open in conversation",
    ],
    "important": [
        "Speak with weight and expectation of being heard",
        "May reference own role or responsibilities",
        "Less tolerant of being dismissed or interrupted",
    ],
    "faithful": [
        "Express loyalty and commitment in relationships",
        "Keep promises and reference shared history",
        "Reliability and consistency in what they say",
    ],
    "satisfied": [
        "Relaxed, content demeanor — no urgency",
        "Reflect positively on recent events or outcomes",
        "Less driven to change things — comfortable with status quo",
    ],
    # ── Peaceful/Calm emotions ──
    "content": [
        "Responses are measured and calm — no emotional extremes",
        "Present-focused rather than worrying about future or past",
        "Quietly pleased with the current state of things",
    ],
    "thoughtful": [
        "Take time before responding — responses feel considered",
        "Ask deeper questions that show genuine interest",
        "Reflect on implications rather than reacting quickly",
    ],
    "intimate": [
        "Share personal details more freely than usual",
        "Use warmer, softer language — fewer formal barriers",
        "Reference shared experiences and inside knowledge",
    ],
    "loving": [
        "Express affection through words, gestures, and attention",
        "Prioritize the other person's wellbeing in conversation",
        "Forgive imperfections easily — generous interpretation",
    ],
    "trusting": [
        "Take others at their word without questioning motives",
        "Share information openly, including vulnerabilities",
        "Relaxed body language — no defensiveness",
    ],
    "nurturing": [
        "Check in on others' wellbeing — 'are you okay?'",
        "Offer help, advice, or comfort proactively",
        "Patient and supportive even when frustrated",
    ],
}
"""Behavioral guidelines per emotion for conversation prompts."""


@dataclass
class ConversationTemplate(BaseTemplate):
    """Template for conversation/dialogue prompts.

    Generates prompts that instruct the LLM to roleplay as an individual
    in a conversation with others, considering emotional state, personality,
    relationships, and situational context.

    Attributes:
        memory_component: Component for memory formatting.
        relationship_component: Component for relationship formatting.
        situation_component: Component for situation formatting.
        style: Conversation style ("natural", "formal", "casual").

    Example:
        >>> template = ConversationTemplate()
        >>> prompt = template.render(
        ...     individual=sarah,
        ...     other_participants=[mike],
        ...     situation=meeting,
        ... )
    """

    memory_component: MemoryComponent = field(default_factory=MemoryComponent)
    relationship_component: RelationshipComponent = field(default_factory=RelationshipComponent)
    situation_component: SituationComponent = field(default_factory=SituationComponent)
    style: str = "natural"

    def render(
        self,
        individual: Any,
        *,
        other_participants: list[Any] | None = None,
        relationships: list[Any] | None = None,
        situation: Situation | Any | None = None,
        memories: list[Any] | None = None,
        trust_level: float = 1.0,
        guidelines: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        """Render a conversation prompt.

        Args:
            individual: The individual to roleplay as.
            other_participants: Other individuals in the conversation.
            relationships: Relationships between participants.
            situation: The situational context.
            memories: Relevant memories to include.
            trust_level: Trust level for memory filtering.
            guidelines: Additional behavioral guidelines.
            **kwargs: Additional template-specific options.

        Returns:
            Complete conversation prompt.
        """
        name = self._get_name(individual)
        emotional_state = self._get_emotional_state(individual)
        traits = self._get_traits(individual)

        # Build sections
        sections = []

        # Identity
        sections.append(self._render_identity(individual))

        # Personality
        if traits:
            sections.append(self._render_personality(traits, name=name))

        # Emotional state
        if emotional_state:
            sections.append(
                self._render_emotional_state(
                    emotional_state,
                    name=name,
                    highlight_dominant=True,
                )
            )

        # Relationships
        if other_participants and relationships:
            rel_text = self.relationship_component.format(
                individual,
                other_participants,
                relationships,
            )
            if rel_text:
                sections.append(rel_text)
        elif other_participants:
            # No existing relationships - describe as new connections
            sections.append(self._render_new_relationships(name, other_participants))

        # Memories
        if memories:
            mem_text = self.memory_component.format(
                memories,
                trust_level=trust_level,
                name=name,
            )
            if mem_text:
                sections.append(mem_text)

        # Situation
        if situation:
            sit_text = self.situation_component.format(situation, name=name)
            if sit_text:
                sections.append(sit_text)

        # Guidelines
        all_guidelines = self._generate_guidelines(emotional_state, traits, guidelines)
        if all_guidelines:
            sections.append(self._render_guidelines(all_guidelines))

        # Response instruction
        sections.append(self._render_conversation_instruction(name))

        return self._join_sections(sections)

    def _render_new_relationships(
        self,
        name: str,
        others: list[Any],
    ) -> str:
        """Render section for new/unknown relationships."""
        other_names = [self._get_name(o) for o in others]

        if len(other_names) == 1:
            return (
                f"## Relationship Context\n"
                f"- {name} is meeting {other_names[0]} for the first time "
                f"and will be cautiously open."
            )

        names_text = ", ".join(other_names[:-1]) + f" and {other_names[-1]}"
        return (
            f"## Relationship Context\n- {name} is meeting {names_text} for the first time and will be cautiously open."
        )

    def _generate_guidelines(
        self,
        emotional_state: EmotionalState | None,
        traits: TraitProfile | None,
        custom_guidelines: list[str] | None,
    ) -> list[str]:
        """Generate behavioral guidelines based on state.

        Now examines the top 3 emotions (not just dominant) and detects
        emotionally complex states where positive and negative emotions
        co-exist — producing guidelines for inner conflict and nuance.

        Args:
            emotional_state: Current emotional state.
            traits: Personality traits.
            custom_guidelines: User-provided guidelines.

        Returns:
            List of behavioral guidelines.
        """
        from personaut.emotions.categories import get_category

        guidelines = []

        # Emotion-based guidelines — consider top 3 emotions, not just dominant
        if emotional_state:
            top_emotions = emotional_state.get_top(3)
            active = [(e, v) for e, v in top_emotions if v >= 0.3]

            if active:
                # Primary emotion guidelines (full set)
                primary_emotion, primary_intensity = active[0]
                if primary_intensity >= 0.4:
                    guidelines.extend(self._get_emotion_guidelines(primary_emotion, primary_intensity))

                # Secondary emotions get lighter guidelines (first guideline only)
                for emotion, intensity in active[1:]:
                    if intensity >= 0.4:
                        secondary_guidelines = self._get_emotion_guidelines(emotion, intensity)
                        if secondary_guidelines:
                            guidelines.append(
                                f"Secondary emotion — {emotion} ({intensity:.0%}): {secondary_guidelines[0]}"
                            )

                # Detect emotionally complex states (mixed valence)
                if len(active) >= 2:
                    categories = set()
                    has_positive = False
                    has_negative = False
                    for e, _v in active:
                        try:
                            cat = get_category(e)
                            categories.add(cat)
                            if cat.is_positive:
                                has_positive = True
                            if cat.is_negative:
                                has_negative = True
                        except KeyError:
                            pass

                    if has_positive and has_negative:
                        guidelines.append(
                            "You are experiencing MIXED EMOTIONS — conflicting "
                            "feelings are present simultaneously. This creates "
                            "subtle tension in how you respond: pauses, "
                            "contradictions caught mid-sentence, saying one thing "
                            "while feeling another. Real people often don't have "
                            "clean emotional responses."
                        )

        # Style-based guidelines
        if self.style == "formal":
            guidelines.append("Use formal language and measured responses")
            guidelines.append("Maintain professional boundaries")
        elif self.style == "casual":
            guidelines.append("Use relaxed, conversational language")
            guidelines.append("Be personable and approachable")
        else:  # natural
            guidelines.append("Respond naturally and authentically")

        # Add custom guidelines
        if custom_guidelines:
            guidelines.extend(custom_guidelines)

        return guidelines

    def _get_emotion_guidelines(
        self,
        emotion: str,
        intensity: float,
    ) -> list[str]:
        """Get behavioral guidelines for an emotion.

        Covers all 36 emotions with psychologically grounded behavioral
        cues.  The raw mapping lives in ``_EMOTION_GUIDELINES`` (module
        constant); this method applies intensity-aware scaling on top.

        Args:
            emotion: The dominant emotion.
            intensity: Emotion intensity.

        Returns:
            List of emotion-specific guidelines.
        """
        base_guidelines = list(_EMOTION_GUIDELINES.get(emotion, []))

        # Intensity-aware scaling
        if intensity >= 0.8 and base_guidelines:
            # At overwhelming intensity, the emotion DOMINATES behavior
            base_guidelines = [f"This emotion is overwhelming — it colors everything: {g}" for g in base_guidelines]
            base_guidelines.insert(0, f"Your {emotion} feeling is so strong it's hard to focus on anything else")
        elif intensity >= 0.6 and base_guidelines:
            # At significant intensity, it's clearly noticeable
            base_guidelines = [f"Noticeably: {g}" for g in base_guidelines]

        return base_guidelines

    def _render_conversation_instruction(self, name: str) -> str:
        """Render the conversation-specific instruction."""
        return f"Respond as {name} would in this conversation."


__all__ = ["ConversationTemplate"]
