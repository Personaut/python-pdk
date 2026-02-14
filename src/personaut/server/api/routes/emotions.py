"""Emotion management API routes.

This module provides endpoints for managing emotional states.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from personaut.server.api.app import get_app_state
from personaut.server.api.schemas import (
    EmotionalStateResponse,
    EmotionHistoryEntry,
    EmotionHistoryResponse,
    EmotionUpdate,
)


router = APIRouter()


def _get_individual_or_404(individual_id: str) -> dict[str, Any]:
    """Get individual or raise 404.

    Args:
        individual_id: Individual ID.

    Returns:
        Individual data.

    Raises:
        HTTPException: If individual not found.
    """
    state = get_app_state()
    if individual_id not in state.individuals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Individual {individual_id} not found",
        )
    result: dict[str, Any] = state.individuals[individual_id]
    return result


def _get_dominant_emotion(emotions: dict[str, float]) -> tuple[str, float] | None:
    """Get the dominant emotion.

    Args:
        emotions: Emotion values.

    Returns:
        Tuple of (emotion_name, value) or None if empty.
    """
    if not emotions:
        return None
    max_emotion = max(emotions.items(), key=lambda x: x[1])
    return (max_emotion[0], max_emotion[1])


def _get_top_emotions(
    emotions: dict[str, float],
    n: int = 5,
) -> list[tuple[str, float]]:
    """Get top N emotions by value.

    Args:
        emotions: Emotion values.
        n: Number of top emotions.

    Returns:
        List of (emotion_name, value) tuples.
    """
    sorted_emotions = sorted(emotions.items(), key=lambda x: -x[1])
    return [(k, v) for k, v in sorted_emotions[:n]]


@router.get(
    "/api/individuals/{individual_id}/emotions",
    response_model=EmotionalStateResponse,
)
async def get_emotions(
    individual_id: str,
) -> EmotionalStateResponse:
    """Get individual's emotional state.

    Args:
        individual_id: Individual ID.

    Returns:
        Emotional state response.
    """
    individual = _get_individual_or_404(individual_id)
    emotions = individual.get("emotional_state", {})

    return EmotionalStateResponse(
        emotions=emotions,
        dominant=_get_dominant_emotion(emotions),
        top_emotions=_get_top_emotions(emotions),
    )


@router.patch(
    "/api/individuals/{individual_id}/emotions",
    response_model=EmotionalStateResponse,
)
async def update_emotions(
    individual_id: str,
    data: EmotionUpdate,
) -> EmotionalStateResponse:
    """Update individual's emotional state.

    Args:
        individual_id: Individual ID.
        data: Emotion update data.

    Returns:
        Updated emotional state.
    """
    individual = _get_individual_or_404(individual_id)
    emotions = individual.get("emotional_state", {})

    # Validate emotion values
    for emotion, value in data.emotions.items():
        if not 0.0 <= value <= 1.0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Emotion value must be between 0 and 1: {emotion}={value}",
            )

    # Apply fill value if specified
    if data.fill is not None:
        for emotion in emotions:
            if emotion not in data.emotions:
                emotions[emotion] = data.fill

    # Update specified emotions
    emotions.update(data.emotions)
    individual["emotional_state"] = emotions
    individual["updated_at"] = datetime.now()

    # Record history
    _record_emotion_history(individual_id, emotions)

    return EmotionalStateResponse(
        emotions=emotions,
        dominant=_get_dominant_emotion(emotions),
        top_emotions=_get_top_emotions(emotions),
    )


@router.post(
    "/api/individuals/{individual_id}/emotions/reset",
    response_model=EmotionalStateResponse,
)
async def reset_emotions(
    individual_id: str,
    value: float = Query(0.0, ge=0.0, le=1.0, description="Reset value"),
) -> EmotionalStateResponse:
    """Reset individual's emotional state.

    Args:
        individual_id: Individual ID.
        value: Value to set all emotions to.

    Returns:
        Reset emotional state.
    """
    individual = _get_individual_or_404(individual_id)
    emotions = individual.get("emotional_state", {})

    # Reset all emotions to the specified value
    for emotion in emotions:
        emotions[emotion] = value

    individual["emotional_state"] = emotions
    individual["updated_at"] = datetime.now()

    # Record history
    _record_emotion_history(individual_id, emotions, trigger="reset")

    return EmotionalStateResponse(
        emotions=emotions,
        dominant=_get_dominant_emotion(emotions),
        top_emotions=_get_top_emotions(emotions),
    )


@router.get(
    "/api/individuals/{individual_id}/emotions/history",
    response_model=EmotionHistoryResponse,
)
async def get_emotion_history(
    individual_id: str,
    limit: int = Query(10, ge=1, le=100, description="Number of entries"),
) -> EmotionHistoryResponse:
    """Get individual's emotion history.

    Args:
        individual_id: Individual ID.
        limit: Maximum number of history entries.

    Returns:
        Emotion history.
    """
    _get_individual_or_404(individual_id)
    state = get_app_state()

    # Get history from state (or empty list)
    history_key = f"emotion_history_{individual_id}"
    history = state.individuals.get(history_key, [])

    # Limit results
    limited_history = history[-limit:]

    return EmotionHistoryResponse(
        individual_id=individual_id,
        history=[EmotionHistoryEntry(**entry) for entry in limited_history],
        total_entries=len(history),
    )


def _record_emotion_history(
    individual_id: str,
    state_dict: dict[str, float],
    trigger: str | None = None,
) -> None:
    """Record an emotion state change in history.

    Args:
        individual_id: Individual ID.
        state_dict: Current emotion state.
        trigger: What triggered the change.
    """
    app_state = get_app_state()
    history_key = f"emotion_history_{individual_id}"

    if history_key not in app_state.individuals:
        app_state.individuals[history_key] = []

    entry = {
        "timestamp": datetime.now(),
        "state": state_dict.copy(),
        "trigger": trigger,
    }
    app_state.individuals[history_key].append(entry)

    # Keep only last 100 entries
    if len(app_state.individuals[history_key]) > 100:
        app_state.individuals[history_key] = app_state.individuals[history_key][-100:]


__all__ = ["router"]
