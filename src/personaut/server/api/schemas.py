"""Pydantic schemas for the Personaut API.

This module defines all request and response schemas for the API endpoints.

Example:
    >>> from personaut.server.api.schemas import IndividualCreate
    >>> data = IndividualCreate(name="Sarah", description="A friendly AI")
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Base Schemas
# ============================================================================


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = {"from_attributes": True, "extra": "ignore"}


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None


# ============================================================================
# Emotion Schemas
# ============================================================================


class EmotionValue(BaseSchema):
    """A single emotion with its value."""

    name: str = Field(..., description="Emotion name (e.g., 'anxious', 'hopeful')")
    value: float = Field(..., ge=0.0, le=1.0, description="Emotion intensity (0-1)")


class EmotionUpdate(BaseSchema):
    """Request to update emotions."""

    emotions: dict[str, float] = Field(
        ...,
        description="Emotions to update with their new values",
    )
    fill: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Value to set for unspecified emotions",
    )


class EmotionalStateResponse(BaseSchema):
    """Response containing emotional state."""

    emotions: dict[str, float] = Field(..., description="All emotions and values")
    dominant: tuple[str, float] | None = Field(
        None,
        description="Dominant emotion and value",
    )
    top_emotions: list[tuple[str, float]] = Field(
        default_factory=list,
        description="Top 5 emotions by value",
    )


class EmotionHistoryEntry(BaseSchema):
    """A single entry in emotion history."""

    timestamp: datetime
    state: dict[str, float]
    trigger: str | None = None


class EmotionHistoryResponse(BaseSchema):
    """Response containing emotion history."""

    individual_id: str
    history: list[EmotionHistoryEntry]
    total_entries: int


# ============================================================================
# Trait Schemas
# ============================================================================


class TraitValue(BaseSchema):
    """A single trait with its value."""

    name: str = Field(..., description="Trait name (e.g., 'warmth', 'openness')")
    value: float = Field(..., ge=0.0, le=1.0, description="Trait value (0-1)")


class TraitUpdate(BaseSchema):
    """Request to update traits."""

    traits: dict[str, float] = Field(
        ...,
        description="Traits to update with their new values",
    )


class TraitProfileResponse(BaseSchema):
    """Response containing trait profile."""

    traits: dict[str, float] = Field(..., description="All traits and values")
    high_traits: list[tuple[str, float]] = Field(
        default_factory=list,
        description="Traits above 0.7",
    )
    low_traits: list[tuple[str, float]] = Field(
        default_factory=list,
        description="Traits below 0.3",
    )


# ============================================================================
# Individual Schemas
# ============================================================================


class IndividualCreate(BaseSchema):
    """Request to create an individual."""

    name: str = Field(..., min_length=1, max_length=100, description="Individual name")
    description: str | None = Field(None, description="Description of the individual")
    # Remember what Uncle Ben said: "With great power comes great
    # responsibility." Don't be a creep!
    age: int | None = Field(
        None,
        ge=18,
        description="Age of the individual in years (must be 18+)",
    )
    individual_type: str = Field(
        "simulated",
        description="Type: simulated, human, or nontracked",
    )
    initial_emotions: dict[str, float] | None = Field(
        None,
        description="Initial emotional state",
    )
    initial_traits: dict[str, float] | None = Field(
        None,
        description="Initial trait values",
    )
    physical_features: dict[str, Any] | None = Field(
        None,
        description="Physical appearance features (height, build, hair, eyes, etc.)",
    )
    generate_portrait: bool = Field(
        False,
        description="Whether to auto-generate a portrait from physical features",
    )
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class IndividualUpdate(BaseSchema):
    """Request to update an individual."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    physical_features: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class IndividualResponse(BaseSchema, TimestampMixin):
    """Response containing individual data."""

    id: str = Field(..., description="Unique identifier")
    name: str
    description: str | None = None
    individual_type: str
    emotional_state: dict[str, float] | None = None
    trait_profile: dict[str, float] | None = None
    physical_features: dict[str, Any] | None = None
    portrait_url: str | None = None
    metadata: dict[str, Any] | None = None


class IndividualListResponse(BaseSchema):
    """Response containing list of individuals."""

    individuals: list[IndividualResponse]
    total: int
    page: int = 1
    page_size: int = 10


# ============================================================================
# Situation Schemas
# ============================================================================


class SituationCreate(BaseSchema):
    """Request to create a situation."""

    description: str = Field(..., min_length=1, description="Situation description")
    modality: str = Field("in_person", description="Communication modality")
    location: str | None = Field(None, description="Physical location")
    context: dict[str, Any] | None = Field(
        None,
        description="Additional situational context",
    )


class SituationUpdate(BaseSchema):
    """Request to update a situation."""

    description: str | None = None
    modality: str | None = None
    location: str | None = None
    context: dict[str, Any] | None = None


class SituationResponse(BaseSchema, TimestampMixin):
    """Response containing situation data."""

    id: str = Field(..., description="Unique identifier")
    description: str
    modality: str
    location: str | None = None
    context: dict[str, Any] | None = None


class SituationListResponse(BaseSchema):
    """Response containing list of situations."""

    situations: list[SituationResponse]
    total: int


# ============================================================================
# Relationship Schemas
# ============================================================================


class TrustUpdate(BaseSchema):
    """Request to update trust between individuals."""

    from_individual: str = Field(..., description="Source individual ID")
    to_individual: str = Field(..., description="Target individual ID")
    change: float = Field(..., ge=-1.0, le=1.0, description="Trust change amount")
    reason: str | None = Field(None, description="Reason for trust change")


class RelationshipCreate(BaseSchema):
    """Request to create a relationship."""

    individual_ids: list[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="IDs of the two individuals",
    )
    initial_trust: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Initial trust level",
    )
    relationship_type: str = Field(
        "acquaintance",
        description="Type of relationship",
    )
    history: str | None = Field(None, description="Relationship history")


class RelationshipResponse(BaseSchema, TimestampMixin):
    """Response containing relationship data."""

    id: str = Field(..., description="Unique identifier")
    individual_ids: list[str]
    trust: dict[str, dict[str, float]] = Field(
        ...,
        description="Bilateral trust matrix",
    )
    relationship_type: str
    history: str | None = None
    shared_memory_ids: list[str] = Field(default_factory=list)


class RelationshipListResponse(BaseSchema):
    """Response containing list of relationships."""

    relationships: list[RelationshipResponse]
    total: int


# ============================================================================
# Session Schemas
# ============================================================================


class SessionCreate(BaseSchema):
    """Request to create a chat session."""

    situation_id: str = Field(..., description="Situation ID for the session")
    individual_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Individual IDs participating",
    )
    human_id: str | None = Field(
        None,
        description="ID of the human participant (if any)",
    )
    metadata: dict[str, Any] | None = Field(None, description="Session metadata")


class SessionResponse(BaseSchema, TimestampMixin):
    """Response containing session data."""

    id: str = Field(..., description="Session ID")
    situation_id: str
    individual_ids: list[str]
    human_id: str | None = None
    active: bool = True
    message_count: int = 0
    metadata: dict[str, Any] | None = None


class SessionListResponse(BaseSchema):
    """Response containing list of sessions."""

    sessions: list[SessionResponse]
    total: int


# ============================================================================
# Message Schemas
# ============================================================================


class MessageCreate(BaseSchema):
    """Request to send a message."""

    content: str = Field(..., min_length=1, description="Message content")
    sender_id: str | None = Field(
        None,
        description="Sender ID (None for human)",
    )
    action: str | None = Field(None, description="Optional action description")


class MessageResponse(BaseSchema):
    """Response containing a message."""

    id: str = Field(..., description="Message ID")
    session_id: str
    sender_id: str | None = None
    sender_name: str
    content: str
    action: str | None = None
    timestamp: datetime
    emotional_state: dict[str, float] | None = None


class MessageListResponse(BaseSchema):
    """Response containing list of messages."""

    messages: list[MessageResponse]
    total: int
    session_id: str


class AIResponseRequest(BaseSchema):
    """Request for AI to generate a response."""

    from_individual_id: str = Field(..., description="Which AI individual responds")
    context: dict[str, Any] | None = Field(
        None,
        description="Additional context for response",
    )


# ============================================================================
# WebSocket Schemas
# ============================================================================


class WebSocketMessage(BaseSchema):
    """Message format for WebSocket communication."""

    type: str = Field(..., description="Message type")
    data: dict[str, Any] = Field(default_factory=dict, description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now)


class EmotionChangeNotification(BaseSchema):
    """Notification of emotional state change."""

    individual_id: str
    previous_state: dict[str, float]
    new_state: dict[str, float]
    trigger: str | None = None


class TriggerActivationNotification(BaseSchema):
    """Notification of trigger activation."""

    individual_id: str
    trigger_description: str
    response_type: str  # 'mask' or 'emotional_state'


# ============================================================================
# Memory Schemas
# ============================================================================


class MemoryCreate(BaseSchema):
    """Request to create a memory for an individual."""

    description: str = Field(..., min_length=1, description="Human-readable description of the memory")
    salience: float = Field(0.5, ge=0.0, le=1.0, description="How important/memorable (0-1)")
    emotional_state: dict[str, float] | None = Field(None, description="Emotional state at time of memory")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata (e.g. tags)")


class MemoryResponse(BaseSchema):
    """Response containing a single memory."""

    id: str = Field(..., description="Unique memory identifier")
    description: str
    owner_id: str
    salience: float = 0.5
    memory_type: str = "individual"
    emotional_state: dict[str, float] | None = None
    metadata: dict[str, Any] | None = None


class MemoryListResponse(BaseSchema):
    """Response containing a list of memories."""

    memories: list[MemoryResponse]
    total: int


class MemorySearchRequest(BaseSchema):
    """Request to search memories."""

    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(10, ge=1, le=50, description="Max results")


class MemorySearchResponse(BaseSchema):
    """Response from memory search."""

    query: str
    results: list[MemoryResponse]
    total: int


# ============================================================================
# Mask Schemas
# ============================================================================


class MaskCreate(BaseSchema):
    """Request to create a mask for an individual."""

    name: str = Field(..., min_length=1, description="Mask name (e.g. 'professional')")
    description: str = Field("", description="Human-readable description")
    emotional_modifications: dict[str, float] = Field(
        default_factory=dict,
        description="Emotion adjustments: positive values increase, negative decrease",
    )
    trigger_situations: list[str] = Field(default_factory=list, description="Keywords that activate this mask")
    active_by_default: bool = Field(False, description="Whether mask is always active")


class MaskResponse(BaseSchema):
    """Response containing a single mask."""

    id: str = Field(..., description="Unique mask identifier")
    name: str
    description: str = ""
    emotional_modifications: dict[str, float] = Field(default_factory=dict)
    trigger_situations: list[str] = Field(default_factory=list)
    active_by_default: bool = False
    owner_id: str = ""


class MaskListResponse(BaseSchema):
    """Response containing a list of masks."""

    masks: list[MaskResponse]
    total: int


# ============================================================================
# Trigger Schemas
# ============================================================================


class TriggerRuleSchema(BaseSchema):
    """A single rule for trigger evaluation."""

    field: str = Field(..., description="Emotion or situational field to check")
    threshold: float = Field(..., description="Threshold value")
    operator: str = Field(">", description="Comparison operator (>, <, >=, <=, ==, !=")


class TriggerCreate(BaseSchema):
    """Request to create a trigger for an individual."""

    description: str = Field(..., min_length=1, description="Trigger description")
    trigger_type: str = Field("emotional", description="Type: 'emotional' or 'situational'")
    rules: list[TriggerRuleSchema] = Field(default_factory=list, description="Rules that define when the trigger fires")
    match_all: bool = Field(True, description="If True, ALL rules must match")
    active: bool = Field(True, description="Whether the trigger is active")
    priority: int = Field(0, description="Priority (higher fires first)")
    keyword_triggers: list[str] = Field(default_factory=list, description="Keywords for situational triggers")
    response_type: str = Field(
        "modifications",
        description="Response type: 'modifications' (emotion changes) or 'mask' (mask name)",
    )
    response_data: dict[str, float] | str | None = Field(None, description="Emotion modifications dict or mask name")


class TriggerResponse(BaseSchema):
    """Response containing a single trigger."""

    id: str = Field(..., description="Unique trigger identifier")
    description: str
    trigger_type: str = "emotional"
    rules: list[TriggerRuleSchema] = Field(default_factory=list)
    match_all: bool = True
    active: bool = True
    priority: int = 0
    keyword_triggers: list[str] = Field(default_factory=list)
    response_type: str = "modifications"
    response_data: dict[str, float] | str | None = None
    owner_id: str = ""


class TriggerListResponse(BaseSchema):
    """Response containing a list of triggers."""

    triggers: list[TriggerResponse]
    total: int


# ============================================================================
# Error Schemas
# ============================================================================


class ErrorResponse(BaseSchema):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional details")


class ValidationErrorDetail(BaseSchema):
    """Detail of a validation error."""

    field: str
    message: str
    value: Any | None = None


class ValidationErrorResponse(BaseSchema):
    """Validation error response."""

    error: str = "validation_error"
    message: str = "Request validation failed"
    errors: list[ValidationErrorDetail]


__all__ = [
    # Base
    "BaseSchema",
    "TimestampMixin",
    # Emotions
    "EmotionValue",
    "EmotionUpdate",
    "EmotionalStateResponse",
    "EmotionHistoryEntry",
    "EmotionHistoryResponse",
    # Traits
    "TraitValue",
    "TraitUpdate",
    "TraitProfileResponse",
    # Individuals
    "IndividualCreate",
    "IndividualUpdate",
    "IndividualResponse",
    "IndividualListResponse",
    # Situations
    "SituationCreate",
    "SituationUpdate",
    "SituationResponse",
    "SituationListResponse",
    # Relationships
    "TrustUpdate",
    "RelationshipCreate",
    "RelationshipResponse",
    "RelationshipListResponse",
    # Sessions
    "SessionCreate",
    "SessionResponse",
    "SessionListResponse",
    # Messages
    "MessageCreate",
    "MessageResponse",
    "MessageListResponse",
    "AIResponseRequest",
    # Memories
    "MemoryCreate",
    "MemoryResponse",
    "MemoryListResponse",
    "MemorySearchRequest",
    "MemorySearchResponse",
    # Masks
    "MaskCreate",
    "MaskResponse",
    "MaskListResponse",
    # Triggers
    "TriggerRuleSchema",
    "TriggerCreate",
    "TriggerResponse",
    "TriggerListResponse",
    # WebSocket
    "WebSocketMessage",
    "EmotionChangeNotification",
    "TriggerActivationNotification",
    # Errors
    "ErrorResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
]
