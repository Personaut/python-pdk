"""Situation management API routes.

This module provides CRUD endpoints for managing situations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from personaut.server.api.app import get_app_state
from personaut.server.api.schemas import (
    SituationCreate,
    SituationListResponse,
    SituationResponse,
    SituationUpdate,
)


router = APIRouter()


@router.get("", response_model=SituationListResponse)
async def list_situations() -> SituationListResponse:
    """List all situations.

    Returns:
        List of situations.
    """
    state = get_app_state()
    all_situations = list(state.situations.values())

    return SituationListResponse(
        situations=[SituationResponse(**sit) for sit in all_situations],
        total=len(all_situations),
    )


@router.post("", response_model=SituationResponse, status_code=status.HTTP_201_CREATED)
async def create_situation(
    data: SituationCreate,
) -> SituationResponse:
    """Create a new situation.

    Args:
        data: Situation creation data.

    Returns:
        Created situation.
    """
    state = get_app_state()

    # Generate unique ID
    situation_id = f"sit_{uuid.uuid4().hex[:8]}"

    # Build situation data
    now = datetime.now()
    situation: dict[str, Any] = {
        "id": situation_id,
        "description": data.description,
        "modality": data.modality,
        "location": data.location,
        "context": data.context or {},
        "created_at": now,
        "updated_at": None,
    }

    # Store
    state.situations[situation_id] = situation

    # Persist
    if state.persistence:
        try:
            state.persistence.save_situation(situation)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist situation %s",
                situation_id,
            )

    return SituationResponse(**situation)


@router.get("/{situation_id}", response_model=SituationResponse)
async def get_situation(
    situation_id: str,
) -> SituationResponse:
    """Get situation by ID.

    Args:
        situation_id: Situation ID.

    Returns:
        Situation data.

    Raises:
        HTTPException: If situation not found.
    """
    state = get_app_state()

    if situation_id not in state.situations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Situation {situation_id} not found",
        )

    return SituationResponse(**state.situations[situation_id])


@router.patch("/{situation_id}", response_model=SituationResponse)
async def update_situation(
    situation_id: str,
    data: SituationUpdate,
) -> SituationResponse:
    """Update situation by ID.

    Args:
        situation_id: Situation ID.
        data: Update data.

    Returns:
        Updated situation.

    Raises:
        HTTPException: If situation not found.
    """
    state = get_app_state()

    if situation_id not in state.situations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Situation {situation_id} not found",
        )

    situation = state.situations[situation_id]

    # Update fields
    if data.description is not None:
        situation["description"] = data.description
    if data.modality is not None:
        situation["modality"] = data.modality
    if data.location is not None:
        situation["location"] = data.location
    if data.context is not None:
        situation["context"] = data.context

    situation["updated_at"] = datetime.now()

    # Persist
    if state.persistence:
        try:
            state.persistence.save_situation(situation)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist situation update %s",
                situation_id,
            )

    return SituationResponse(**situation)


@router.delete("/{situation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_situation(
    situation_id: str,
) -> None:
    """Delete situation by ID.

    Args:
        situation_id: Situation ID.

    Raises:
        HTTPException: If situation not found.
    """
    state = get_app_state()

    if situation_id not in state.situations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Situation {situation_id} not found",
        )

    del state.situations[situation_id]

    # Persist
    if state.persistence:
        try:
            state.persistence.delete_situation(situation_id)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist situation delete %s",
                situation_id,
            )


@router.put("/{situation_id}/modality", response_model=SituationResponse)
async def update_modality(
    situation_id: str,
    modality: str,
) -> SituationResponse:
    """Update situation modality.

    Args:
        situation_id: Situation ID.
        modality: New modality value.

    Returns:
        Updated situation.

    Raises:
        HTTPException: If situation not found or invalid modality.
    """
    state = get_app_state()

    if situation_id not in state.situations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Situation {situation_id} not found",
        )

    valid_modalities = [
        "in_person",
        "text_message",
        "email",
        "phone_call",
        "video_call",
    ]

    if modality not in valid_modalities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid modality. Must be one of: {valid_modalities}",
        )

    situation = state.situations[situation_id]
    situation["modality"] = modality
    situation["updated_at"] = datetime.now()

    # Persist
    if state.persistence:
        try:
            state.persistence.save_situation(situation)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist modality update %s",
                situation_id,
            )

    return SituationResponse(**situation)


@router.get("/{situation_id}/modality")
async def get_modality(
    situation_id: str,
) -> dict[str, Any]:
    """Get situation modality configuration.

    Args:
        situation_id: Situation ID.

    Returns:
        Modality information.

    Raises:
        HTTPException: If situation not found.
    """
    state = get_app_state()

    if situation_id not in state.situations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Situation {situation_id} not found",
        )

    situation = state.situations[situation_id]

    # Return modality with configuration options
    modality = situation.get("modality", "text_message")
    modality_config = {
        "modality": modality,
        "is_synchronous": modality in ["in_person", "phone_call", "video_call"],
        "has_visual_cues": modality in ["in_person", "video_call"],
        "has_audio_cues": modality in ["in_person", "phone_call", "video_call"],
        "available_modalities": [
            {"value": "in_person", "label": "In Person", "icon": "👥"},
            {"value": "text_message", "label": "Text Message", "icon": "💬"},
            {"value": "email", "label": "Email", "icon": "📧"},
            {"value": "phone_call", "label": "Phone Call", "icon": "📞"},
            {"value": "video_call", "label": "Video Call", "icon": "📹"},
        ],
    }

    return modality_config


__all__ = ["router"]
