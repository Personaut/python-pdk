#!/usr/bin/env python3
"""Example 15: LangChain Integration

This example demonstrates how to use Personaut personas inside LangChain
chains and agents. It provides three integration patterns:

  1. PersonaChatModel  — wraps any LangChain LLM with a Personaut persona
     so every response is influenced by traits, emotions, masks, and memory.
  2. PersonaMemory     — plugs Personaut's salience-weighted memory into
     LangChain's memory interface.
  3. A complete chain   — wires both together in a ConversationChain.

Requirements:
    pip install personaut langchain langchain-google-genai   # or langchain-openai

Usage:
    GOOGLE_API_KEY=your_key python 15_langchain_integration.py

    Or run without an API key to see the offline integration demo only.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Iterator

from personaut import create_individual
from personaut.emotions.state import EmotionalState
from personaut.masks.mask import create_mask
from personaut.memory.memory import Memory
from personaut.prompts import PromptBuilder
from personaut.triggers.emotional import create_emotional_trigger


# ═══════════════════════════════════════════════════════════════════════
# 1. PersonaChatModel — LangChain ChatModel wrapper
# ═══════════════════════════════════════════════════════════════════════

def _check_langchain() -> bool:
    """Return True if langchain-core is installed."""
    try:
        import langchain_core  # noqa: F401
        return True
    except ImportError:
        return False


HAS_LANGCHAIN = _check_langchain()

if HAS_LANGCHAIN:
    from langchain_core.callbacks import CallbackManagerForLLMRun
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import (
        AIMessage,
        BaseMessage,
        HumanMessage,
        SystemMessage,
    )
    from langchain_core.outputs import ChatGeneration, ChatResult

    class PersonaChatModel(BaseChatModel):
        """A LangChain ChatModel that injects Personaut persona context.

        This wraps an existing LangChain chat model and automatically
        prepends a persona-aware system prompt built from the individual's
        emotional state, personality traits, active masks, and memories.

        Example::

            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
            persona_llm = PersonaChatModel(
                individual=sarah,
                inner_llm=llm,
            )
            # Use anywhere you'd use a regular ChatModel
            response = persona_llm.invoke("How are you today?")
        """

        individual: Any
        inner_llm: BaseChatModel
        include_emotions: bool = True
        include_traits: bool = True
        include_memories: bool = True
        memories: list[Any] = []

        class Config:
            arbitrary_types_allowed = True

        @property
        def _llm_type(self) -> str:
            return "personaut-persona"

        @property
        def _identifying_params(self) -> dict[str, Any]:
            return {
                "persona_name": self.individual.name,
                "inner_llm": self.inner_llm._llm_type,
            }

        def _build_system_prompt(self) -> str:
            """Build a persona system prompt using Personaut's PromptBuilder."""
            builder = PromptBuilder().with_individual(self.individual)

            if self.include_emotions:
                builder = builder.with_emotional_state(
                    self.individual.get_emotional_state()
                )
            if self.include_traits:
                builder = builder.with_traits(
                    self.individual.traits
                )
            if self.include_memories and self.memories:
                builder = builder.with_memories(self.memories)

            return builder.using_template("conversation").build()

        def _generate(
            self,
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: CallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            """Generate a response with persona context injected."""
            # Build persona system prompt
            system_prompt = self._build_system_prompt()

            # Prepend system message with persona context
            augmented: list[BaseMessage] = [
                SystemMessage(content=system_prompt),
                *messages,
            ]

            # Delegate to the inner LLM
            result = self.inner_llm._generate(
                augmented, stop=stop, run_manager=run_manager, **kwargs,
            )

            # Update emotional state based on the conversation
            last_human = None
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_human = msg.content
                    break

            if last_human:
                self._update_emotions(last_human)

            return result

        def _update_emotions(self, user_message: str) -> None:
            """Nudge the individual's emotional state based on message sentiment.

            This is a simplified heuristic. In production you'd use the PDK's
            trigger/mask evaluation or an LLM-based sentiment classifier.
            """
            lower = user_message.lower()
            state = self.individual.get_emotional_state()

            # Simple keyword-based emotional nudges
            positive = ["thank", "great", "love", "happy", "awesome", "wonderful"]
            negative = ["angry", "upset", "hate", "terrible", "frustrated", "sad"]
            anxious = ["worried", "nervous", "scared", "afraid", "anxious"]

            if any(w in lower for w in positive):
                state.update_emotion("cheerful", min(state.get_emotion("cheerful") + 0.1, 1.0))
                state.update_emotion("content", min(state.get_emotion("content") + 0.05, 1.0))
            elif any(w in lower for w in negative):
                state.update_emotion("hurt", min(state.get_emotion("hurt") + 0.1, 1.0))
                state.update_emotion("cheerful", max(state.get_emotion("cheerful") - 0.1, 0.0))
            elif any(w in lower for w in anxious):
                state.update_emotion("anxious", min(state.get_emotion("anxious") + 0.15, 1.0))

    # ═══════════════════════════════════════════════════════════════════
    # 2. PersonaMemory — LangChain Memory backed by Personaut
    # ═══════════════════════════════════════════════════════════════════

    from langchain_core.memory import BaseMemory

    class PersonaMemory(BaseMemory):
        """A LangChain Memory that stores and retrieves Personaut memories.

        Each conversation turn is stored as a Personaut Memory object with
        salience scoring. When loaded, the most salient memories are returned
        as context for the next LLM call.

        Example::

            memory = PersonaMemory(individual=sarah, k=5)
            chain = ConversationChain(llm=persona_llm, memory=memory)
        """

        individual: Any
        memories: list[Any] = []
        k: int = 5  # number of memories to include in context
        memory_key: str = "history"
        human_prefix: str = "Human"
        ai_prefix: str = "AI"
        _turn_count: int = 0

        class Config:
            arbitrary_types_allowed = True

        @property
        def memory_variables(self) -> list[str]:
            return [self.memory_key]

        def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, str]:
            """Load the most salient memories as conversation history."""
            # Sort by salience (highest first) and take top-k
            sorted_mems = sorted(
                self.memories,
                key=lambda m: m.metadata.get("salience", 0.5),
                reverse=True,
            )
            top = sorted_mems[: self.k]

            # Format as conversation history
            lines = []
            for mem in top:
                lines.append(mem.description)

            return {self.memory_key: "\n".join(lines)}

        def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
            """Save a conversation turn as a Personaut Memory."""
            self._turn_count += 1
            human_input = inputs.get("input", "")
            ai_output = outputs.get("output", "")

            # Calculate salience (later turns and longer exchanges are more salient)
            base_salience = 0.5
            length_bonus = min(len(human_input) / 500, 0.3)
            recency_bonus = min(self._turn_count * 0.05, 0.2)
            salience = min(base_salience + length_bonus + recency_bonus, 1.0)

            mem = Memory(
                description=f"{self.human_prefix}: {human_input}\n{self.ai_prefix}: {ai_output}",
                metadata={"salience": salience, "type": "conversation"},
            )
            self.memories.append(mem)

            # Also attach to the PersonaChatModel if it's using the same individual
            if hasattr(self.individual, "_memories"):
                self.individual._memories.append(mem)

        def clear(self) -> None:
            """Clear all memories."""
            self.memories.clear()
            self._turn_count = 0


# ═══════════════════════════════════════════════════════════════════════
# Demo code (runs with or without LangChain installed)
# ═══════════════════════════════════════════════════════════════════════

def create_demo_persona():
    """Create a richly configured persona for the demo."""
    therapist = create_individual(
        name="Dr. Elena Santos",
        traits={
            "warmth": 0.9,
            "sensitivity": 0.85,
            "emotional_stability": 0.8,
            "reasoning": 0.8,
            "openness_to_change": 0.7,
            "social_boldness": 0.6,
            "dominance": 0.35,
        },
        emotional_state={
            "content": 0.8,
            "satisfied": 0.6,
            "hopeful": 0.5,
        },
        metadata={
            "occupation": "Clinical psychologist",
            "specialty": "Cognitive behavioral therapy",
            "years_experience": "15",
            "speaking_style": "Warm, reflective, uses open-ended questions",
        },
    )

    # Add a professional mask
    professional_mask = create_mask(
        name="Professional Composure",
        emotional_modifications={"anxious": -0.3, "content": 0.2},
        trigger_situations=["therapy session", "client interaction"],
        active_by_default=True,
        description="Maintains professional calm during sessions",
    )
    therapist.add_mask(professional_mask)

    # Add an empathy trigger
    empathy_trigger = create_emotional_trigger(
        description="Heightened empathy when client expresses distress",
        rules=[{"field": "concerned", "threshold": 0.3, "operator": ">"}],
        match_all=False,
    )
    therapist.add_trigger(empathy_trigger)

    # Add formative memories
    therapist.add_memory(Memory(
        description="Completed PhD in Clinical Psychology at Stanford with focus on trauma-informed CBT approaches.",
        metadata={"salience": 0.9, "type": "biographical"},
    ))
    therapist.add_memory(Memory(
        description="A patient once said 'You were the first person who made me feel heard.' This became a guiding principle.",
        metadata={"salience": 0.95, "type": "formative"},
    ))
    therapist.add_memory(Memory(
        description="Believes strongly that therapeutic alliance is the most important factor in positive outcomes.",
        metadata={"salience": 0.85, "type": "professional"},
    ))

    return therapist


def demo_offline(therapist):
    """Show the persona prompt construction (no LLM needed)."""
    print("=" * 60)
    print("Offline Demo: Persona Prompt Construction")
    print("=" * 60)

    # Build a conversation prompt
    prompt = (
        PromptBuilder()
        .with_individual(therapist)
        .with_emotional_state(therapist.get_emotional_state())
        .with_traits(therapist.traits)
        .with_memories(therapist.get_memories())
        .with_guidelines([
            "Use reflective listening techniques",
            "Ask open-ended questions",
            "Validate the client's experience before offering perspectives",
        ])
        .using_template("conversation")
        .build()
    )

    print("\n📋 Generated System Prompt:")
    print("-" * 40)
    # Show first 800 chars to keep output manageable
    preview = prompt[:800]
    if len(prompt) > 800:
        preview += f"\n... [{len(prompt) - 800} more characters]"
    print(preview)

    # Show emotional state
    print(f"\n🎭 Active Emotions:")
    state = therapist.get_emotional_state()
    emotions = state.to_dict()
    active = {k: round(v, 2) for k, v in emotions.items() if v > 0}
    for emotion, intensity in sorted(active.items(), key=lambda x: -x[1]):
        bar = "█" * int(intensity * 20)
        print(f"   {emotion:<15} {intensity:.2f} {bar}")

    # Show masks
    masks = therapist.masks
    if masks:
        print(f"\n🎭 Active Masks:")
        for mask in masks:
            print(f"   • {mask.name}: {mask.description}")

    # Show memories
    memories = therapist.get_memories()
    if memories:
        print(f"\n💭 Memories ({len(memories)}):")
        for mem in memories:
            salience = mem.metadata.get("salience", 0.5)
            salience_bar = "●" * int(salience * 5) + "○" * (5 - int(salience * 5))
            print(f"   [{salience_bar}] {mem.description[:70]}...")

    print()


def demo_langchain(therapist):
    """Run a live LangChain conversation with the persona."""
    print("=" * 60)
    print("Live Demo: LangChain + Personaut Conversation")
    print("=" * 60)

    # Try to get an LLM
    llm = None
    if os.environ.get("GOOGLE_API_KEY"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
            print("\n✅ Using Google Gemini via LangChain")
        except ImportError:
            print("\n⚠️  langchain-google-genai not installed. pip install langchain-google-genai")
    elif os.environ.get("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o-mini")
            print("\n✅ Using OpenAI via LangChain")
        except ImportError:
            print("\n⚠️  langchain-openai not installed. pip install langchain-openai")

    if llm is None:
        print("\n⚠️  No LLM API key found. Skipping live demo.")
        print("   Set GOOGLE_API_KEY or OPENAI_API_KEY to run the live demo.")
        return

    # Create the PersonaChatModel
    persona_llm = PersonaChatModel(
        individual=therapist,
        inner_llm=llm,
        memories=therapist.get_memories(),
    )

    # Create PersonaMemory
    memory = PersonaMemory(individual=therapist, k=5)

    print(f"\n🧑‍⚕️ Chatting with {therapist.name}")
    print(f"   (Traits: warmth={therapist.get_trait('warmth'):.1f}, "
          f"sensitivity={therapist.get_trait('sensitivity'):.1f})")
    print("-" * 40)

    # Simulate a therapy conversation
    test_messages = [
        "Hi Dr. Santos. I've been feeling really overwhelmed at work lately.",
        "I keep thinking I'm not good enough and everyone will find out.",
        "Thank you, that actually helps to hear. What should I try first?",
    ]

    for user_msg in test_messages:
        print(f"\n👤 Patient: {user_msg}")

        # Invoke the persona-aware model
        response = persona_llm.invoke([HumanMessage(content=user_msg)])

        print(f"\n🧑‍⚕️ Dr. Santos: {response.content}")

        # Save to memory
        memory.save_context(
            {"input": user_msg},
            {"output": response.content},
        )

        # Show emotional state shift
        state = therapist.get_emotional_state()
        emotions = state.to_dict()
        active = {k: round(v, 2) for k, v in emotions.items() if v > 0}
        top_3 = sorted(active.items(), key=lambda x: -x[1])[:3]
        emotion_str = ", ".join(f"{k}={v}" for k, v in top_3)
        print(f"   📊 Emotional state: [{emotion_str}]")

    # Show accumulated memories
    print(f"\n💭 Accumulated Memories: {len(memory.memories)}")
    for i, mem in enumerate(memory.memories, 1):
        salience = mem.metadata.get("salience", 0.5)
        print(f"   {i}. [salience={salience:.2f}] {mem.description[:60]}...")

    print("\n✅ LangChain integration demo completed successfully!")


def demo_integration_code():
    """Show code snippets for common integration patterns."""
    print("\n" + "=" * 60)
    print("Integration Patterns (Copy-Paste Ready)")
    print("=" * 60)

    print("""
┌─────────────────────────────────────────────────────────┐
│  Pattern 1: Drop-in Persona for any LangChain chain    │
└─────────────────────────────────────────────────────────┘

    from personaut import create_individual
    from langchain_google_genai import ChatGoogleGenerativeAI

    # Create persona
    npc = create_individual(
        name="Gruff the Blacksmith",
        traits={"warmth": 0.3, "dominance": 0.8, "sensitivity": 0.2},
        emotional_state={"critical": 0.4, "energetic": 0.7},
    )

    # Wrap any LangChain LLM with the persona
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    persona_llm = PersonaChatModel(individual=npc, inner_llm=llm)

    # Use in any chain — the persona context is injected automatically
    from langchain_core.prompts import ChatPromptTemplate
    chain = ChatPromptTemplate.from_messages([
        ("human", "{input}")
    ]) | persona_llm
    response = chain.invoke({"input": "Can you forge me a sword?"})

┌─────────────────────────────────────────────────────────┐
│  Pattern 2: Persona with persistent memory              │
└─────────────────────────────────────────────────────────┘

    memory = PersonaMemory(individual=npc, k=10)

    # Every call saves context; past interactions influence future ones
    memory.save_context(
        {"input": "I need a legendary weapon"},
        {"output": "Hmph. Legendary weapons aren't cheap, adventurer."},
    )

    # Later, the memory is loaded into the prompt
    context = memory.load_memory_variables({})
    # => {"history": "Human: I need a legendary weapon\\nAI: Hmph..."}

┌─────────────────────────────────────────────────────────┐
│  Pattern 3: Persona as a LangGraph agent node           │
└─────────────────────────────────────────────────────────┘

    # PersonaChatModel works anywhere a ChatModel is expected
    from langgraph.graph import StateGraph

    def persona_node(state):
        response = persona_llm.invoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(...)
    graph.add_node("npc", persona_node)

┌─────────────────────────────────────────────────────────┐
│  Pattern 4: Multiple personas in one chain              │
└─────────────────────────────────────────────────────────┘

    teacher = create_individual(
        name="Ms. Chen",
        traits={"warmth": 0.8, "reasoning": 0.9, "dominance": 0.5},
    )
    student = create_individual(
        name="Jake",
        traits={"warmth": 0.6, "reasoning": 0.4, "liveliness": 0.9},
        emotional_state={"confused": 0.6, "thoughtful": 0.4},
    )

    teacher_llm = PersonaChatModel(individual=teacher, inner_llm=llm)
    student_llm = PersonaChatModel(individual=student, inner_llm=llm)

    # Simulate a tutoring session
    question = "What is photosynthesis?"
    teacher_response = teacher_llm.invoke([HumanMessage(content=question)])
    student_response = student_llm.invoke([
        HumanMessage(content=teacher_response.content)
    ])
""")
    print("✅ See the full source code for implementation details.")


def main() -> None:
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   Example 15: LangChain + Personaut Integration         ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()

    # Create the demo persona
    therapist = create_demo_persona()
    print(f"✅ Created persona: {therapist.name}")
    print(f"   Traits: warmth={therapist.get_trait('warmth'):.1f}, "
          f"sensitivity={therapist.get_trait('sensitivity'):.1f}, "
          f"emotional_stability={therapist.get_trait('emotional_stability'):.1f}")
    print(f"   Masks: {len(therapist.masks)}")
    print(f"   Memories: {len(therapist.get_memories())}")

    # Always run the offline demo
    print()
    demo_offline(therapist)

    # Run code pattern examples
    demo_integration_code()

    # Run live demo if LangChain + API key are available
    if HAS_LANGCHAIN:
        print()
        demo_langchain(therapist)
    else:
        print("\n⚠️  LangChain not installed. Install with:")
        print("   pip install langchain-core langchain-google-genai")
        print("   Then re-run this example for the live demo.")

    print("\n✅ Example 15 completed successfully!")


if __name__ == "__main__":
    main()
