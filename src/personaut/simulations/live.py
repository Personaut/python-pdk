"""Live simulation for Personaut PDK.

This module provides the LiveSimulation class for real-time
interactive simulations.

Example:
    >>> from personaut.simulations.live import LiveSimulation
    >>> simulation = LiveSimulation(
    ...     situation=situation,
    ...     individuals=[ai_friend, human],
    ...     simulation_type=SimulationType.LIVE_CONVERSATION,
    ... )
    >>> simulation.start_simulator(port=5000)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from personaut.simulations.simulation import Simulation


@dataclass
class ChatMessage:
    """A single message in a live chat session.

    Attributes:
        sender: Name of the message sender.
        content: Message content.
        action: Optional action description (for in-person/video).
        timestamp: When the message was sent.
        emotional_state: Sender's emotional state at time of message.
        metadata: Additional message metadata.

    Example:
        >>> message = ChatMessage(
        ...     sender="Sarah",
        ...     content="Hello! How are you?",
        ... )
    """

    sender: str
    content: str
    action: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    emotional_state: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "sender": self.sender,
            "content": self.content,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "emotional_state": self.emotional_state,
            "metadata": self.metadata,
        }


@dataclass
class ChatSession:
    """An interactive chat session with a simulated individual.

    Attributes:
        session_id: Unique session identifier.
        simulation: Reference to the parent simulation.
        messages: List of messages in the session.
        started_at: When the session started.
        ended_at: When the session ended (if ended).

    Example:
        >>> chat = simulation.create_chat_session()
        >>> response = chat.send("Hello!")
    """

    session_id: str
    simulation: LiveSimulation
    messages: list[ChatMessage] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None

    # Internal state
    _active: bool = field(default=True, repr=False)

    def send(self, content: str) -> ChatMessage:
        """Send a message and get a response.

        Args:
            content: Message content to send.

        Returns:
            Response ChatMessage from the AI.

        Raises:
            RuntimeError: If session is not active.
        """
        if not self._active:
            msg = "Session is not active"
            raise RuntimeError(msg)

        # Get the human participant
        human = self._get_human_participant()
        human_name = self.simulation._get_individual_name(human) if human else "User"

        # Record user message
        user_message = ChatMessage(
            sender=human_name,
            content=content,
        )
        self.messages.append(user_message)

        # Generate AI response
        ai_response = self._generate_response(content)

        # Record AI message
        self.messages.append(ai_response)

        return ai_response

    def send_action(self, action: str) -> ChatMessage:
        """Send an action without dialogue.

        Args:
            action: Description of the action.

        Returns:
            Response ChatMessage from the AI.

        Raises:
            RuntimeError: If session is not active.
        """
        if not self._active:
            msg = "Session is not active"
            raise RuntimeError(msg)

        human = self._get_human_participant()
        human_name = self.simulation._get_individual_name(human) if human else "User"

        # Record action
        action_message = ChatMessage(
            sender=human_name,
            content="",
            action=action,
        )
        self.messages.append(action_message)

        # Generate AI response to action
        ai_response = self._generate_response_to_action(action)
        self.messages.append(ai_response)

        return ai_response

    def get_state(self) -> dict[str, Any]:
        """Get current session state.

        Returns:
            Dictionary with current state information.
        """
        ai = self._get_ai_participant()
        emotional_state = self.simulation._get_emotional_state(ai) if ai else None

        emotions = {}
        if emotional_state:
            if hasattr(emotional_state, "to_dict"):
                emotions = emotional_state.to_dict()
            elif isinstance(emotional_state, dict):
                emotions = emotional_state

        dominant = "neutral"
        if emotions:
            dominant = max(emotions.items(), key=lambda x: x[1])[0]

        return {
            "session_id": self.session_id,
            "active": self._active,
            "message_count": len(self.messages),
            "emotional_state": emotions,
            "dominant_emotion": dominant,
            "active_mask": None,  # TODO: Implement mask tracking
            "duration": (datetime.now() - self.started_at).total_seconds(),
        }

    def get_history(self) -> list[dict[str, Any]]:
        """Get message history.

        Returns:
            List of message dictionaries.
        """
        return [msg.to_dict() for msg in self.messages]

    def advance_time(self, hours: float = 0, minutes: float = 0) -> None:
        """Simulate time passage.

        Args:
            hours: Hours to advance.
            minutes: Minutes to advance.
        """
        # In a real implementation, this would affect emotional state decay
        # and other time-dependent factors
        pass

    def end(self) -> None:
        """End the chat session."""
        self._active = False
        self.ended_at = datetime.now()

    def _get_human_participant(self) -> Any | None:
        """Get the human participant."""
        for individual in self.simulation.individuals:
            if self.simulation._is_human(individual):
                return individual
        return None

    def _get_ai_participant(self) -> Any | None:
        """Get the AI participant."""
        for individual in self.simulation.individuals:
            if not self.simulation._is_human(individual):
                return individual
        return None

    def _generate_response(self, user_message: str) -> ChatMessage:
        """Generate AI response to a message.

        Args:
            user_message: The user's message.

        Returns:
            AI response message.
        """
        ai = self._get_ai_participant()
        ai_name = self.simulation._get_individual_name(ai) if ai else "AI"
        emotional_state = self.simulation._get_emotional_state(ai) if ai else None

        emotions = {}
        if emotional_state:
            if hasattr(emotional_state, "to_dict"):
                emotions = emotional_state.to_dict()
            elif isinstance(emotional_state, dict):
                emotions = emotional_state

        # Generate placeholder response
        # In a real implementation, this would use the LLM
        dominant = "cheerful"
        if emotions:
            dominant = max(emotions.items(), key=lambda x: x[1])[0]

        content = self._generate_contextual_response(user_message, dominant)

        return ChatMessage(
            sender=ai_name,
            content=content,
            emotional_state=emotions,
        )

    def _generate_response_to_action(self, action: str) -> ChatMessage:
        """Generate AI response to an action.

        Args:
            action: The action description.

        Returns:
            AI response message.
        """
        ai = self._get_ai_participant()
        ai_name = self.simulation._get_individual_name(ai) if ai else "AI"
        emotional_state = self.simulation._get_emotional_state(ai) if ai else None

        emotions = {}
        if emotional_state:
            if hasattr(emotional_state, "to_dict"):
                emotions = emotional_state.to_dict()
            elif isinstance(emotional_state, dict):
                emotions = emotional_state

        # Generate response to action
        content = "*responds to the action* That's interesting!"

        return ChatMessage(
            sender=ai_name,
            content=content,
            action=f"*notices {action}*",
            emotional_state=emotions,
        )

    def _generate_contextual_response(
        self,
        user_message: str,
        dominant_emotion: str,
    ) -> str:
        """Generate a contextual response based on emotion.

        Args:
            user_message: The user's message.
            dominant_emotion: Dominant emotion of the AI.

        Returns:
            Generated response.
        """
        # Simple response generation based on emotion
        if dominant_emotion in ("cheerful", "trusting", "loving"):
            return "That's great to hear! Tell me more about that."
        elif dominant_emotion in ("thoughtful", "creative"):
            return "Oh, that's fascinating! I'd love to know more details."
        elif dominant_emotion in ("anxious", "helpless"):
            return "I see... I hope everything works out okay."
        elif dominant_emotion in ("excited", "energetic"):
            return "Wow, that's so exciting! What happened next?"
        else:
            return "I understand. What else is on your mind?"


@dataclass
class LiveSimulation(Simulation):
    """Simulation for real-time interactive conversations.

    Provides a live chat interface where users can interact with
    simulated individuals in real-time.

    Attributes:
        show_emotions: Whether to display emotion panel.
        show_triggers: Whether to show trigger notifications.
        show_masks: Whether to show mask indicators.
        show_memories: Whether to show retrieved memories.
        typing_delay: Whether to simulate typing time.
        typing_speed: Speed of simulated typing.
        auto_save: Whether to auto-save conversation history.

    Example:
        >>> simulation = LiveSimulation(
        ...     situation=situation,
        ...     individuals=[ai_friend, human],
        ...     simulation_type=SimulationType.LIVE_CONVERSATION,
        ... )
        >>> simulation.start_simulator(port=5000)
    """

    show_emotions: bool = True
    show_triggers: bool = True
    show_masks: bool = True
    show_memories: bool = False
    typing_delay: bool = True
    typing_speed: str = "normal"
    auto_save: bool = True

    # Internal state
    _sessions: dict[str, ChatSession] = field(default_factory=dict, repr=False)
    _server_running: bool = field(default=False, repr=False)

    def _generate(self, run_index: int = 0, **options: Any) -> str:
        """Generate is not used for live simulations.

        Args:
            run_index: Index of this run.
            **options: Additional options.

        Returns:
            Information message.
        """
        return "Live simulations are interactive. Use start_simulator() or create_chat_session() instead."

    def start_simulator(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        debug: bool = False,
        theme: str = "dark",
        **options: Any,
    ) -> None:
        """Start the interactive simulator server.

        Args:
            host: Host address to bind.
            port: Port number.
            debug: Enable debug mode.
            theme: UI theme ('light', 'dark', 'system').
            **options: Additional server options.

        Note:
            This method blocks until the server is stopped.
        """
        # Store options
        self.show_emotions = options.get("show_emotions", self.show_emotions)
        self.show_triggers = options.get("show_triggers", self.show_triggers)
        self.show_masks = options.get("show_masks", self.show_masks)
        self.typing_delay = options.get("typing_delay", self.typing_delay)
        self.auto_save = options.get("auto_save", self.auto_save)

        self._server_running = True

        # In a real implementation, this would start a Flask/FastAPI server
        # For now, just print information
        print(f"Starting live simulator on http://{host}:{port}")
        print(f"Theme: {theme}")
        print(f"Show emotions: {self.show_emotions}")
        print(f"Show triggers: {self.show_triggers}")
        print("")
        print("Use create_chat_session() for programmatic control.")

    def stop_simulator(self) -> None:
        """Stop the simulator server."""
        self._server_running = False
        print("Simulator stopped.")

    def create_chat_session(self) -> ChatSession:
        """Create a new chat session.

        Returns:
            New ChatSession for interactive messaging.

        Example:
            >>> chat = simulation.create_chat_session()
            >>> response = chat.send("Hello!")
            >>> print(response.content)
        """
        import uuid

        session_id = f"session_{uuid.uuid4().hex[:8]}"

        session = ChatSession(
            session_id=session_id,
            simulation=self,
        )

        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> ChatSession | None:
        """Get an existing session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            ChatSession if found, None otherwise.
        """
        return self._sessions.get(session_id)

    def save_session(self, session: ChatSession, path: str | Path) -> None:
        """Save a session to disk.

        Args:
            session: Session to save.
            path: File path to save to.
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "session_id": session.session_id,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "situation": {
                "description": getattr(self.situation, "description", ""),
                "modality": getattr(self.situation, "modality", None),
            },
            "participants": [
                {
                    "name": self._get_individual_name(ind),
                    "is_human": self._is_human(ind),
                }
                for ind in self.individuals
            ],
            "messages": session.get_history(),
        }

        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_session(self, path: str | Path) -> ChatSession:
        """Load a session from disk.

        Args:
            path: File path to load from.

        Returns:
            Loaded ChatSession.

        Raises:
            FileNotFoundError: If path doesn't exist.
        """
        input_path = Path(path)
        data = json.loads(input_path.read_text(encoding="utf-8"))

        session = ChatSession(
            session_id=data["session_id"],
            simulation=self,
            started_at=datetime.fromisoformat(data["started_at"]),
            ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
        )

        # Restore messages
        for msg_data in data.get("messages", []):
            message = ChatMessage(
                sender=msg_data["sender"],
                content=msg_data["content"],
                action=msg_data.get("action"),
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                emotional_state=msg_data.get("emotional_state", {}),
                metadata=msg_data.get("metadata", {}),
            )
            session.messages.append(message)

        self._sessions[session.session_id] = session
        return session

    def _is_human(self, individual: Any) -> bool:
        """Check if an individual is a human participant.

        Args:
            individual: Individual to check.

        Returns:
            True if the individual is human.
        """
        if hasattr(individual, "is_human"):
            return bool(individual.is_human)
        if hasattr(individual, "individual_type"):
            ind_type = str(individual.individual_type).lower()
            return "human" in ind_type
        if isinstance(individual, dict):
            return bool(individual.get("is_human", False))
        return False


__all__ = [
    "ChatMessage",
    "ChatSession",
    "LiveSimulation",
]
