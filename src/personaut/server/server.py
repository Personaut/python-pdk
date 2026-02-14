"""LiveInteractionServer for Personaut.

This module provides the main server class that coordinates
the FastAPI backend and Flask web UI.

Example:
    >>> from personaut.server import LiveInteractionServer
    >>> server = LiveInteractionServer()
    >>> server.add_individual(my_individual)
    >>> server.start(api_port=8000, ui_port=5000)
"""

from __future__ import annotations

import threading
from typing import Any


class LiveInteractionServer:
    """Server for live persona interactions.

    This class manages both the FastAPI API server and the Flask
    web UI server, providing a unified interface for live interactions.

    Attributes:
        individuals: Dictionary of registered individuals.
        situations: Dictionary of registered situations.
        config: Server configuration.

    Example:
        >>> server = LiveInteractionServer()
        >>> server.add_individual(sarah)
        >>> server.add_situation(coffee_shop)
        >>> server.start(api_port=8000)
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the server.

        Args:
            config: Optional configuration dictionary.
        """
        self.individuals: dict[str, Any] = {}
        self.situations: dict[str, Any] = {}
        self.relationships: dict[str, Any] = {}
        self.config = config or {}

        self._api_thread: threading.Thread | None = None
        self._ui_thread: threading.Thread | None = None
        self._api_server: Any = None
        self._running = False

    def add_individual(self, individual: Any, id_override: str | None = None) -> str:
        """Register an individual with the server.

        Args:
            individual: The individual to register.
            id_override: Optional ID override.

        Returns:
            The individual's ID.

        Example:
            >>> individual_id = server.add_individual(sarah)
        """
        ind_id = id_override or getattr(individual, "id", None)
        if ind_id is None:
            import uuid

            ind_id = f"ind_{uuid.uuid4().hex[:8]}"

        self.individuals[ind_id] = individual
        return ind_id

    def add_situation(self, situation: Any, id_override: str | None = None) -> str:
        """Register a situation with the server.

        Args:
            situation: The situation to register.
            id_override: Optional ID override.

        Returns:
            The situation's ID.
        """
        sit_id = id_override or getattr(situation, "id", None)
        if sit_id is None:
            import uuid

            sit_id = f"sit_{uuid.uuid4().hex[:8]}"

        self.situations[sit_id] = situation
        return sit_id

    def add_relationship(self, relationship: Any, id_override: str | None = None) -> str:
        """Register a relationship with the server.

        Args:
            relationship: The relationship to register.
            id_override: Optional ID override.

        Returns:
            The relationship's ID.
        """
        rel_id = id_override or getattr(relationship, "id", None)
        if rel_id is None:
            import uuid

            rel_id = f"rel_{uuid.uuid4().hex[:8]}"

        self.relationships[rel_id] = relationship
        return rel_id

    def start(
        self,
        api_port: int = 8000,
        ui_port: int | None = None,
        host: str = "127.0.0.1",
        api_only: bool = False,
        blocking: bool = True,
    ) -> None:
        """Start the server(s).

        Args:
            api_port: Port for the FastAPI server.
            ui_port: Port for the Flask UI server (if not api_only).
            host: Host to bind to.
            api_only: If True, only start the API server.
            blocking: If True, block until shutdown.

        Example:
            >>> server.start(api_port=8000, ui_port=5000)
        """
        self._running = True

        # Load .env file if present (provides GOOGLE_API_KEY, etc.)
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        # Start API server
        self._start_api(host=host, port=api_port, blocking=blocking and api_only)

        # Start UI server if requested
        if not api_only and ui_port:
            self._start_ui(host=host, port=ui_port, blocking=blocking)

    def _start_api(
        self,
        host: str,
        port: int,
        blocking: bool = False,
    ) -> None:
        """Start the FastAPI server.

        Args:
            host: Host to bind to.
            port: Port to bind to.
            blocking: If True, block until shutdown.
        """
        try:
            import uvicorn

            from personaut.server.api.app import create_app

            app = create_app()

            if blocking:
                uvicorn.run(app, host=host, port=port)
            else:
                config = uvicorn.Config(app, host=host, port=port, log_level="info")
                server = uvicorn.Server(config)
                self._api_server = server

                self._api_thread = threading.Thread(target=server.run)
                self._api_thread.start()

        except ImportError as e:
            msg = "FastAPI/uvicorn not installed. Install with: pip install personaut[server]"
            raise ImportError(msg) from e

    def _start_ui(
        self,
        host: str,
        port: int,
        blocking: bool = False,
    ) -> None:
        """Start the Flask UI server.

        Args:
            host: Host to bind to.
            port: Port to bind to.
            blocking: If True, block until shutdown.
        """
        try:
            from personaut.server.ui.app import create_ui_app

            ui_app = create_ui_app()

            if blocking:
                ui_app.run(host=host, port=port, debug=False)
            else:
                self._ui_thread = threading.Thread(target=lambda: ui_app.run(host=host, port=port, debug=False))
                self._ui_thread.start()

        except ImportError as e:
            msg = "Flask not installed. Install with: pip install personaut[server]"
            raise ImportError(msg) from e

    def stop(self) -> None:
        """Stop the server(s) gracefully.

        This method signals the servers to stop and waits for threads
        to complete. For async servers, it triggers shutdown events.
        """
        self._running = False

        # Signal API server to stop
        if self._api_server is not None:
            self._api_server.should_exit = True

        # Wait for threads to finish (with timeout)
        if self._api_thread is not None and self._api_thread.is_alive():
            self._api_thread.join(timeout=5.0)
            self._api_thread = None

        if self._ui_thread is not None and self._ui_thread.is_alive():
            # Flask doesn't have a clean shutdown mechanism in threads
            # It will stop when the process ends
            self._ui_thread = None

        self._api_server = None

    def is_running(self) -> bool:
        """Check if the server is running.

        Returns:
            True if the server is running.
        """
        return self._running

    def get_api_url(self, port: int = 8000, host: str = "127.0.0.1") -> str:
        """Get the API base URL.

        Args:
            port: API port.
            host: API host.

        Returns:
            The API base URL.
        """
        return f"http://{host}:{port}/api"

    def get_ui_url(self, port: int = 5000, host: str = "127.0.0.1") -> str:
        """Get the UI base URL.

        Args:
            port: UI port.
            host: UI host.

        Returns:
            The UI base URL.
        """
        return f"http://{host}:{port}"


class LiveInteractionClient:
    """Client for interacting with a LiveInteractionServer.

    This class provides a Python interface for the server's REST API.

    Example:
        >>> client = LiveInteractionClient("http://localhost:8000/api")
        >>> individuals = client.list_individuals()
    """

    def __init__(self, base_url: str = "http://localhost:8000/api") -> None:
        """Initialize the client.

        Args:
            base_url: Base URL of the API.
        """
        self.base_url = base_url.rstrip("/")
        self._session: Any = None

    def _get_session(self) -> Any:
        """Get or create an HTTP session."""
        if self._session is None:
            try:
                import httpx

                self._session = httpx.Client(base_url=self.base_url)
            except ImportError as e:
                msg = "httpx not installed. Install with: pip install httpx"
                raise ImportError(msg) from e
        return self._session

    def list_individuals(self) -> list[dict[str, Any]]:
        """List all individuals.

        Returns:
            List of individual data.
        """
        session = self._get_session()
        response = session.get("/individuals")
        response.raise_for_status()
        result: list[dict[str, Any]] = response.json()["individuals"]
        return result

    def get_individual(self, individual_id: str) -> dict[str, Any]:
        """Get an individual by ID.

        Args:
            individual_id: Individual ID.

        Returns:
            Individual data.
        """
        session = self._get_session()
        response = session.get(f"/individuals/{individual_id}")
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def create_individual(self, **data: Any) -> dict[str, Any]:
        """Create a new individual.

        Args:
            **data: Individual creation data.

        Returns:
            Created individual data.
        """
        session = self._get_session()
        response = session.post("/individuals", json=data)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def update_emotions(
        self,
        individual_id: str,
        emotions: dict[str, float],
        fill: float | None = None,
    ) -> dict[str, Any]:
        """Update an individual's emotions.

        Args:
            individual_id: Individual ID.
            emotions: Emotions to update.
            fill: Optional fill value for unspecified emotions.

        Returns:
            Updated emotional state.
        """
        session = self._get_session()
        data: dict[str, Any] = {"emotions": emotions}
        if fill is not None:
            data["fill"] = fill
        response = session.patch(f"/individuals/{individual_id}/emotions", json=data)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def create_session(
        self,
        situation_id: str,
        individual_ids: list[str],
        human_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new chat session.

        Args:
            situation_id: Situation ID.
            individual_ids: Individual IDs to include.
            human_id: Optional human participant ID.

        Returns:
            Created session data.
        """
        session = self._get_session()
        data = {
            "situation_id": situation_id,
            "individual_ids": individual_ids,
            "human_id": human_id,
        }
        response = session.post("/sessions", json=data)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def send_message(
        self,
        session_id: str,
        content: str,
        sender_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a message in a session.

        Args:
            session_id: Session ID.
            content: Message content.
            sender_id: Optional sender ID.

        Returns:
            Created message data.
        """
        session = self._get_session()
        data = {"content": content, "sender_id": sender_id}
        response = session.post(f"/sessions/{session_id}/messages", json=data)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Get all messages in a session.

        Args:
            session_id: Session ID.

        Returns:
            List of messages.
        """
        session = self._get_session()
        response = session.get(f"/sessions/{session_id}/messages")
        response.raise_for_status()
        result: list[dict[str, Any]] = response.json()["messages"]
        return result

    def close(self) -> None:
        """Close the client session."""
        if self._session is not None:
            self._session.close()
            self._session = None


__all__ = [
    "LiveInteractionClient",
    "LiveInteractionServer",
]
