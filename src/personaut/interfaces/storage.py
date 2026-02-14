"""Storage Protocol and base classes for Personaut PDK.

This module defines the Storage Protocol that all storage implementations must follow,
providing a consistent interface for persisting individuals, memories, relationships,
and other entity types.

Example:
    >>> from personaut.interfaces.storage import Storage
    >>> class MyStorage(Storage):
    ...     def save_individual(self, individual: dict) -> str:
    ...         # Implementation
    ...         pass
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, Protocol, TypeVar, runtime_checkable


# Type variable for generic entity operations
T = TypeVar("T", bound=dict[str, Any])


@runtime_checkable
class Storage(Protocol):
    """Protocol defining the storage interface for Personaut entities.

    All storage implementations (SQLite, file-based, etc.) must implement
    this protocol to ensure consistent CRUD operations across the system.

    The protocol supports:
    - Individuals (personas with traits, emotions, memories)
    - Relationships (connections between individuals)
    - Situations (interaction contexts)
    - Sessions (conversation history)
    - Memories (individual and shared memories)
    """

    # ========================
    # Individual Operations
    # ========================

    @abstractmethod
    def save_individual(self, individual: dict[str, Any]) -> str:
        """Save an individual to storage.

        Args:
            individual: Individual data dictionary containing at minimum:
                - name: str
                - individual_type: str ("simulated", "human", etc.)

        Returns:
            The ID of the saved individual (generated if not provided).
        """
        ...

    @abstractmethod
    def get_individual(self, individual_id: str) -> dict[str, Any] | None:
        """Retrieve an individual by ID.

        Args:
            individual_id: Unique identifier of the individual.

        Returns:
            Individual data dictionary, or None if not found.
        """
        ...

    @abstractmethod
    def list_individuals(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """List individuals with optional filtering.

        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            **filters: Optional filters (e.g., individual_type="simulated").

        Returns:
            List of individual data dictionaries.
        """
        ...

    @abstractmethod
    def update_individual(
        self,
        individual_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update an existing individual.

        Args:
            individual_id: ID of the individual to update.
            updates: Dictionary of fields to update.

        Returns:
            Updated individual data, or None if not found.
        """
        ...

    @abstractmethod
    def delete_individual(self, individual_id: str) -> bool:
        """Delete an individual from storage.

        Args:
            individual_id: ID of the individual to delete.

        Returns:
            True if deleted, False if not found.
        """
        ...

    # ========================
    # Relationship Operations
    # ========================

    @abstractmethod
    def save_relationship(self, relationship: dict[str, Any]) -> str:
        """Save a relationship to storage.

        Args:
            relationship: Relationship data containing:
                - individual_a: str (ID of first individual)
                - individual_b: str (ID of second individual)
                - relationship_type: str (optional)

        Returns:
            The ID of the saved relationship.
        """
        ...

    @abstractmethod
    def get_relationship(self, relationship_id: str) -> dict[str, Any] | None:
        """Retrieve a relationship by ID.

        Args:
            relationship_id: Unique identifier of the relationship.

        Returns:
            Relationship data dictionary, or None if not found.
        """
        ...

    @abstractmethod
    def list_relationships(
        self,
        individual_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List relationships, optionally filtered by individual.

        Args:
            individual_id: Optional ID to filter relationships involving this individual.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            List of relationship data dictionaries.
        """
        ...

    @abstractmethod
    def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship from storage.

        Args:
            relationship_id: ID of the relationship to delete.

        Returns:
            True if deleted, False if not found.
        """
        ...

    # ========================
    # Situation Operations
    # ========================

    @abstractmethod
    def save_situation(self, situation: dict[str, Any]) -> str:
        """Save a situation to storage.

        Args:
            situation: Situation data containing:
                - description: str
                - modality: str (optional)
                - location: str (optional)

        Returns:
            The ID of the saved situation.
        """
        ...

    @abstractmethod
    def get_situation(self, situation_id: str) -> dict[str, Any] | None:
        """Retrieve a situation by ID."""
        ...

    @abstractmethod
    def list_situations(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List all situations."""
        ...

    @abstractmethod
    def delete_situation(self, situation_id: str) -> bool:
        """Delete a situation from storage."""
        ...

    # ========================
    # Session Operations
    # ========================

    @abstractmethod
    def save_session(self, session: dict[str, Any]) -> str:
        """Save a session to storage.

        Args:
            session: Session data containing:
                - individual_id: str
                - situation_id: str (optional)

        Returns:
            The ID of the saved session.
        """
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve a session by ID."""
        ...

    @abstractmethod
    def list_sessions(
        self,
        individual_id: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List sessions with optional filtering."""
        ...

    @abstractmethod
    def end_session(self, session_id: str) -> bool:
        """Mark a session as ended."""
        ...

    # ========================
    # Message Operations
    # ========================

    @abstractmethod
    def save_message(
        self,
        session_id: str,
        message: dict[str, Any],
    ) -> str:
        """Save a message to a session.

        Args:
            session_id: ID of the session.
            message: Message data containing:
                - sender: str
                - content: str

        Returns:
            The ID of the saved message.
        """
        ...

    @abstractmethod
    def list_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List messages for a session."""
        ...

    # ========================
    # Memory Operations
    # ========================

    @abstractmethod
    def save_memory(
        self,
        individual_id: str,
        memory: dict[str, Any],
    ) -> str:
        """Save a memory for an individual.

        Args:
            individual_id: ID of the individual.
            memory: Memory data containing:
                - content: str
                - memory_type: str (optional)
                - importance: float (optional)

        Returns:
            The ID of the saved memory.
        """
        ...

    @abstractmethod
    def list_memories(
        self,
        individual_id: str,
        memory_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List memories for an individual."""
        ...

    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        ...

    # ========================
    # Lifecycle Operations
    # ========================

    @abstractmethod
    def close(self) -> None:
        """Close the storage connection and clean up resources."""
        ...


class BaseStorage:
    """Base class providing common storage functionality.

    Provides utility methods that can be shared across storage implementations.
    """

    def _generate_id(self, prefix: str = "id") -> str:
        """Generate a unique ID with optional prefix.

        Args:
            prefix: Prefix for the ID (e.g., "ind" for individuals).

        Returns:
            A unique identifier string.
        """
        import uuid

        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def _now(self) -> datetime:
        """Get the current timestamp."""
        return datetime.now()

    def _to_dict(self, entity: Any) -> dict[str, Any]:
        """Convert an entity to a dictionary if necessary."""
        if isinstance(entity, dict):
            return entity
        if hasattr(entity, "to_dict"):
            result: dict[str, Any] = entity.to_dict()
            return result
        if hasattr(entity, "__dict__"):
            return dict(entity.__dict__)
        raise TypeError(f"Cannot convert {type(entity)} to dict")


__all__ = ["BaseStorage", "Storage"]
