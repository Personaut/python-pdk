"""Trigger management API routes.

Provides CRUD endpoints for individual triggers (conditional activators).
Triggers are stored as dicts in the individual's dict under a 'triggers'
key, consistent with the dict-based storage pattern used across the API.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from personaut.server.api.app import get_app_state
from personaut.server.api.schemas import (
    TriggerCreate,
    TriggerListResponse,
    TriggerResponse,
    TriggerRuleSchema,
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


def _ensure_triggers_list(ind: dict[str, Any]) -> list[dict[str, Any]]:
    """Ensure the individual dict has a 'triggers' list."""
    if "triggers" not in ind or not isinstance(ind.get("triggers"), list):
        ind["triggers"] = []
    triggers: list[dict[str, Any]] = ind["triggers"]
    return triggers


def _trigger_dict_to_response(trigger: dict[str, Any], owner_id: str) -> TriggerResponse:
    """Convert a trigger dict to a TriggerResponse schema.

    Handles both:
    - PDK to_dict() format: type, response={type, data}
    - API schema format: trigger_type, response_type, response_data
    """
    rules = [
        TriggerRuleSchema(
            field=r.get("field", ""),
            threshold=r.get("threshold", 0.0),
            operator=r.get("operator", ">"),
        )
        for r in trigger.get("rules", [])
    ]

    # Extract trigger type from either format
    trigger_type = trigger.get("trigger_type") or trigger.get("type", "emotional")

    # Extract response from either format
    response_type = trigger.get("response_type", "modifications")
    response_data = trigger.get("response_data")

    # PDK format stores response as nested dict: {"type": "mask", "data": {...}}
    pdk_response = trigger.get("response")
    if pdk_response and isinstance(pdk_response, dict):
        response_type = pdk_response.get("type", "modifications")
        response_data = pdk_response.get("data")

    return TriggerResponse(
        id=trigger.get("id", ""),
        description=trigger.get("description", ""),
        trigger_type=trigger_type,
        rules=rules,
        match_all=trigger.get("match_all", True),
        active=trigger.get("active", True),
        priority=trigger.get("priority", 0),
        keyword_triggers=trigger.get("keyword_triggers", []),
        response_type=response_type,
        response_data=response_data,
        owner_id=owner_id,
    )


# ---------------------------------------------------------------------------
# Endpoints  (mounted at /api/individuals/{individual_id}/triggers)
# ---------------------------------------------------------------------------


@router.get(
    "/api/individuals/{individual_id}/triggers",
    response_model=TriggerListResponse,
    summary="List triggers for an individual",
)
async def list_triggers(individual_id: str) -> TriggerListResponse:
    """Return all triggers belonging to this individual."""
    ind = _get_individual(individual_id)
    triggers = _ensure_triggers_list(ind)

    return TriggerListResponse(
        triggers=[_trigger_dict_to_response(t, individual_id) for t in triggers],
        total=len(triggers),
    )


@router.post(
    "/api/individuals/{individual_id}/triggers",
    response_model=TriggerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a trigger to an individual",
)
async def create_trigger(
    individual_id: str,
    body: TriggerCreate,
) -> TriggerResponse:
    """Create a new trigger and attach it to the individual."""
    ind = _get_individual(individual_id)
    triggers = _ensure_triggers_list(ind)

    # Validate trigger type
    if body.trigger_type not in ("emotional", "situational"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid trigger_type: '{body.trigger_type}'. Must be 'emotional' or 'situational'.",
        )

    trigger_id = f"trig_{uuid.uuid4().hex[:8]}"
    trigger: dict[str, Any] = {
        "id": trigger_id,
        "description": body.description,
        "trigger_type": body.trigger_type,
        "rules": [r.model_dump() for r in body.rules],
        "match_all": body.match_all,
        "active": body.active,
        "priority": body.priority,
        "keyword_triggers": body.keyword_triggers,
        "response_type": body.response_type,
        "response_data": body.response_data if isinstance(body.response_data, (dict, str)) else None,
        "owner_id": individual_id,
    }

    triggers.append(trigger)

    # Persist the updated individual (with new trigger) to the database
    state = get_app_state()
    if state.persistence is not None:
        try:
            state.persistence.save_individual(ind)
        except Exception:
            logger.warning(
                "Failed to persist trigger %s to DB",
                trigger_id,
                exc_info=True,
            )

    logger.info(
        "Created %s trigger %s for %s: %s (%d rules)",
        body.trigger_type,
        trigger_id,
        individual_id,
        body.description[:60],
        len(body.rules),
    )
    return _trigger_dict_to_response(trigger, individual_id)


@router.get(
    "/api/individuals/{individual_id}/triggers/{trigger_id}",
    response_model=TriggerResponse,
    summary="Get a specific trigger",
)
async def get_trigger(individual_id: str, trigger_id: str) -> TriggerResponse:
    """Retrieve a single trigger by ID."""
    ind = _get_individual(individual_id)
    triggers = _ensure_triggers_list(ind)

    for t in triggers:
        if t.get("id") == trigger_id:
            return _trigger_dict_to_response(t, individual_id)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trigger {trigger_id} not found",
    )


@router.patch(
    "/api/individuals/{individual_id}/triggers/{trigger_id}/toggle",
    response_model=TriggerResponse,
    summary="Toggle a trigger active/inactive",
)
async def toggle_trigger(individual_id: str, trigger_id: str) -> TriggerResponse:
    """Toggle a trigger's active state."""
    ind = _get_individual(individual_id)
    triggers = _ensure_triggers_list(ind)

    for t in triggers:
        if t.get("id") == trigger_id:
            t["active"] = not t.get("active", True)
            logger.info(
                "Toggled trigger %s to %s for %s",
                trigger_id,
                "active" if t["active"] else "inactive",
                individual_id,
            )
            return _trigger_dict_to_response(t, individual_id)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Trigger {trigger_id} not found",
    )


@router.delete(
    "/api/individuals/{individual_id}/triggers/{trigger_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a trigger",
)
async def delete_trigger(individual_id: str, trigger_id: str) -> None:
    """Remove a trigger from the individual."""
    ind = _get_individual(individual_id)
    triggers = _ensure_triggers_list(ind)

    original_count = len(triggers)
    ind["triggers"] = [t for t in triggers if t.get("id") != trigger_id]

    if len(ind["triggers"]) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trigger {trigger_id} not found",
        )

    logger.info("Deleted trigger %s from %s", trigger_id, individual_id)


__all__ = ["router"]
