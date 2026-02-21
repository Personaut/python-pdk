"""Mask management API routes.

Provides CRUD endpoints for individual masks (contextual personas).
Masks are stored as dicts in the individual's dict under a 'masks'
key, consistent with the dict-based storage pattern used across the API.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from personaut.server.api.app import get_app_state
from personaut.server.api.schemas import (
    MaskCreate,
    MaskListResponse,
    MaskResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_individual(individual_id: str) -> dict[str, Any]:
    """Look up an individual dict or raise 404."""
    state = get_app_state()
    ind = state.individuals.get(individual_id)
    if ind is None or not isinstance(ind, dict) or "id" not in ind:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Individual {individual_id} not found",
        )
    result: dict[str, Any] = ind
    return result


def _ensure_masks_list(ind: dict[str, Any]) -> list[dict[str, Any]]:
    """Ensure the individual dict has a 'masks' list."""
    if "masks" not in ind or not isinstance(ind.get("masks"), list):
        ind["masks"] = []
    masks: list[dict[str, Any]] = ind["masks"]
    return masks


def _mask_dict_to_response(mask: dict[str, Any], owner_id: str) -> MaskResponse:
    """Convert a mask dict to a MaskResponse schema."""
    return MaskResponse(
        id=mask.get("id", ""),
        name=mask.get("name", ""),
        description=mask.get("description", ""),
        emotional_modifications=mask.get("emotional_modifications", {}),
        trigger_situations=mask.get("trigger_situations", []),
        active_by_default=mask.get("active_by_default", False),
        owner_id=owner_id,
    )


# ---------------------------------------------------------------------------
# Endpoints  (mounted at /api/individuals/{individual_id}/masks)
# ---------------------------------------------------------------------------


@router.get(
    "/api/individuals/{individual_id}/masks",
    response_model=MaskListResponse,
    summary="List masks for an individual",
)
async def list_masks(individual_id: str) -> MaskListResponse:
    """Return all masks belonging to this individual."""
    ind = _get_individual(individual_id)
    masks = _ensure_masks_list(ind)

    return MaskListResponse(
        masks=[_mask_dict_to_response(m, individual_id) for m in masks],
        total=len(masks),
    )


@router.post(
    "/api/individuals/{individual_id}/masks",
    response_model=MaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a mask to an individual",
)
async def create_mask(
    individual_id: str,
    body: MaskCreate,
) -> MaskResponse:
    """Create a new mask and attach it to the individual."""
    ind = _get_individual(individual_id)
    masks = _ensure_masks_list(ind)

    # Validate emotional modifications are within bounds
    for emotion, value in body.emotional_modifications.items():
        if not -1.0 <= value <= 1.0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Modification for '{emotion}' must be between -1.0 and 1.0, got {value}",
            )

    mask_id = f"mask_{uuid.uuid4().hex[:8]}"
    mask: dict[str, Any] = {
        "id": mask_id,
        "name": body.name,
        "description": body.description,
        "emotional_modifications": body.emotional_modifications,
        "trigger_situations": body.trigger_situations,
        "active_by_default": body.active_by_default,
        "owner_id": individual_id,
    }

    masks.append(mask)

    # Persist the updated individual (with new mask) to the database
    state = get_app_state()
    if state.persistence is not None:
        try:
            state.persistence.save_individual(ind)
        except Exception:
            logger.warning(
                "Failed to persist mask %s to DB",
                mask_id,
                exc_info=True,
            )

    logger.info(
        "Created mask %s for %s: %s (%d mods, %d triggers)",
        mask_id,
        individual_id,
        body.name,
        len(body.emotional_modifications),
        len(body.trigger_situations),
    )
    return _mask_dict_to_response(mask, individual_id)


@router.get(
    "/api/individuals/{individual_id}/masks/{mask_id}",
    response_model=MaskResponse,
    summary="Get a specific mask",
)
async def get_mask(individual_id: str, mask_id: str) -> MaskResponse:
    """Retrieve a single mask by ID."""
    ind = _get_individual(individual_id)
    masks = _ensure_masks_list(ind)

    for m in masks:
        if m.get("id") == mask_id:
            return _mask_dict_to_response(m, individual_id)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Mask {mask_id} not found",
    )


@router.delete(
    "/api/individuals/{individual_id}/masks/{mask_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a mask",
)
async def delete_mask(individual_id: str, mask_id: str) -> None:
    """Remove a mask from the individual."""
    ind = _get_individual(individual_id)
    masks = _ensure_masks_list(ind)

    original_count = len(masks)
    ind["masks"] = [m for m in masks if m.get("id") != mask_id]

    if len(ind["masks"]) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mask {mask_id} not found",
        )

    logger.info("Deleted mask %s from %s", mask_id, individual_id)


__all__ = ["router"]
