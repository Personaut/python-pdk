"""FastAPI application package for Personaut.

This package provides the FastAPI-based REST API for managing
individuals, emotions, situations, relationships, and sessions.

Example:
    >>> from personaut.server.api import create_app
    >>> app = create_app()
"""

from __future__ import annotations

from personaut.server.api.app import AppState, app, create_app, get_app_state
from personaut.server.api.schemas import (
    # Base
    BaseSchema,
    # Emotions
    EmotionalStateResponse,
    EmotionHistoryEntry,
    EmotionHistoryResponse,
    EmotionUpdate,
    EmotionValue,
    # Errors
    ErrorResponse,
    # Individuals
    IndividualCreate,
    IndividualListResponse,
    IndividualResponse,
    IndividualUpdate,
    # Messages
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    # Relationships
    RelationshipCreate,
    RelationshipListResponse,
    RelationshipResponse,
    # Sessions
    SessionCreate,
    SessionListResponse,
    SessionResponse,
    # Situations
    SituationCreate,
    SituationListResponse,
    SituationResponse,
    SituationUpdate,
    TimestampMixin,
    # Traits
    TraitProfileResponse,
    TraitUpdate,
    TraitValue,
    TrustUpdate,
    ValidationErrorResponse,
)


__all__ = [
    # App
    "app",
    "create_app",
    "get_app_state",
    "AppState",
    # Base schemas
    "BaseSchema",
    "TimestampMixin",
    # Emotion schemas
    "EmotionValue",
    "EmotionUpdate",
    "EmotionalStateResponse",
    "EmotionHistoryEntry",
    "EmotionHistoryResponse",
    # Trait schemas
    "TraitValue",
    "TraitUpdate",
    "TraitProfileResponse",
    # Individual schemas
    "IndividualCreate",
    "IndividualUpdate",
    "IndividualResponse",
    "IndividualListResponse",
    # Situation schemas
    "SituationCreate",
    "SituationUpdate",
    "SituationResponse",
    "SituationListResponse",
    # Relationship schemas
    "TrustUpdate",
    "RelationshipCreate",
    "RelationshipResponse",
    "RelationshipListResponse",
    # Session schemas
    "SessionCreate",
    "SessionResponse",
    "SessionListResponse",
    # Message schemas
    "MessageCreate",
    "MessageResponse",
    "MessageListResponse",
    # Error schemas
    "ErrorResponse",
    "ValidationErrorResponse",
]
