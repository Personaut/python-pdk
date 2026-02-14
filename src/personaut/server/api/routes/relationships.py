"""Relationship management API routes.

This module provides CRUD endpoints for managing relationships.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from personaut.server.api.app import get_app_state
from personaut.server.api.schemas import (
    RelationshipCreate,
    RelationshipListResponse,
    RelationshipResponse,
    TrustUpdate,
)


router = APIRouter()


def _get_individual_or_404(individual_id: str) -> dict[str, Any]:
    """Get individual or raise 404."""
    state = get_app_state()
    if individual_id not in state.individuals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Individual {individual_id} not found",
        )
    result: dict[str, Any] = state.individuals[individual_id]
    return result


@router.get("", response_model=RelationshipListResponse)
async def list_relationships() -> RelationshipListResponse:
    """List all relationships.

    Returns:
        List of relationships.
    """
    state = get_app_state()
    all_relationships = list(state.relationships.values())

    return RelationshipListResponse(
        relationships=[RelationshipResponse(**rel) for rel in all_relationships],
        total=len(all_relationships),
    )


@router.post("", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    data: RelationshipCreate,
) -> RelationshipResponse:
    """Create a new relationship.

    Args:
        data: Relationship creation data.

    Returns:
        Created relationship.
    """
    state = get_app_state()

    # Validate individuals exist
    for ind_id in data.individual_ids:
        _get_individual_or_404(ind_id)

    # Generate unique ID
    relationship_id = f"rel_{uuid.uuid4().hex[:8]}"

    # Build bilateral trust matrix
    ind1, ind2 = data.individual_ids
    trust: dict[str, dict[str, float]] = {
        ind1: {ind2: data.initial_trust},
        ind2: {ind1: data.initial_trust},
    }

    # Build relationship data
    now = datetime.now()
    relationship: dict[str, Any] = {
        "id": relationship_id,
        "individual_ids": data.individual_ids,
        "trust": trust,
        "relationship_type": data.relationship_type,
        "history": data.history,
        "shared_memory_ids": [],
        "created_at": now,
        "updated_at": None,
    }

    # Store
    state.relationships[relationship_id] = relationship

    # Persist
    if state.persistence:
        try:
            # Map in-memory format → persistence format
            state.persistence.save_relationship(
                {
                    "id": relationship_id,
                    "individual_a": ind1,
                    "individual_b": ind2,
                    "relationship_type": data.relationship_type,
                    "trust_levels": trust,
                    "shared_memories": [],
                    "metadata": {"history": data.history},
                    "created_at": now,
                }
            )
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist relationship %s",
                relationship_id,
            )

    return RelationshipResponse(**relationship)


@router.get("/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship(
    relationship_id: str,
) -> RelationshipResponse:
    """Get relationship by ID.

    Args:
        relationship_id: Relationship ID.

    Returns:
        Relationship data.

    Raises:
        HTTPException: If relationship not found.
    """
    state = get_app_state()

    if relationship_id not in state.relationships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship {relationship_id} not found",
        )

    return RelationshipResponse(**state.relationships[relationship_id])


@router.post("/{relationship_id}/trust", response_model=RelationshipResponse)
async def update_trust(
    relationship_id: str,
    data: TrustUpdate,
) -> RelationshipResponse:
    """Update trust between individuals in a relationship.

    Args:
        relationship_id: Relationship ID.
        data: Trust update data.

    Returns:
        Updated relationship.

    Raises:
        HTTPException: If relationship not found or individuals not in relationship.
    """
    state = get_app_state()

    if relationship_id not in state.relationships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship {relationship_id} not found",
        )

    relationship = state.relationships[relationship_id]

    # Validate individuals are in relationship
    if data.from_individual not in relationship["individual_ids"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Individual {data.from_individual} not in relationship",
        )
    if data.to_individual not in relationship["individual_ids"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Individual {data.to_individual} not in relationship",
        )

    # Update trust
    trust = relationship["trust"]
    if data.from_individual not in trust:
        trust[data.from_individual] = {}

    current = trust[data.from_individual].get(data.to_individual, 0.5)
    new_value = max(0.0, min(1.0, current + data.change))
    trust[data.from_individual][data.to_individual] = new_value

    relationship["updated_at"] = datetime.now()

    # Persist
    if state.persistence:
        try:
            ind_ids = relationship["individual_ids"]
            state.persistence.save_relationship(
                {
                    "id": relationship_id,
                    "individual_a": ind_ids[0],
                    "individual_b": ind_ids[1],
                    "relationship_type": relationship.get("relationship_type"),
                    "trust_levels": relationship["trust"],
                    "shared_memories": relationship.get("shared_memories", []),
                    "metadata": {"history": relationship.get("history")},
                    "created_at": relationship.get("created_at"),
                }
            )
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist trust update %s",
                relationship_id,
            )

    return RelationshipResponse(**relationship)


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    relationship_id: str,
) -> None:
    """Delete relationship by ID.

    Args:
        relationship_id: Relationship ID.

    Raises:
        HTTPException: If relationship not found.
    """
    state = get_app_state()

    if relationship_id not in state.relationships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship {relationship_id} not found",
        )

    del state.relationships[relationship_id]

    # Persist
    if state.persistence:
        try:
            state.persistence.delete_relationship(relationship_id)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist relationship delete %s",
                relationship_id,
            )


# ============================================================================
# Shared Memory Endpoints
# ============================================================================


@router.get("/{relationship_id}/memories")
async def list_shared_memories(
    relationship_id: str,
) -> dict[str, Any]:
    """List shared memories for a relationship.

    Args:
        relationship_id: Relationship ID.

    Returns:
        List of shared memories.

    Raises:
        HTTPException: If relationship not found.
    """
    state = get_app_state()

    if relationship_id not in state.relationships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship {relationship_id} not found",
        )

    relationship = state.relationships[relationship_id]
    memories = relationship.get("shared_memories", [])

    return {
        "relationship_id": relationship_id,
        "memories": memories,
        "total": len(memories),
    }


@router.post("/{relationship_id}/memories", status_code=status.HTTP_201_CREATED)
async def add_shared_memory(
    relationship_id: str,
    content: str,
    category: str = "general",
    importance: float = 0.5,
) -> dict[str, Any]:
    """Add a shared memory to a relationship.

    Args:
        relationship_id: Relationship ID.
        content: Memory content.
        category: Memory category (e.g., "event", "conversation", "milestone").
        importance: Importance level from 0.0 to 1.0.

    Returns:
        Created memory.

    Raises:
        HTTPException: If relationship not found.
    """
    state = get_app_state()

    if relationship_id not in state.relationships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship {relationship_id} not found",
        )

    relationship = state.relationships[relationship_id]

    # Initialize memories list if not present
    if "shared_memories" not in relationship:
        relationship["shared_memories"] = []

    # Create memory entry
    import uuid

    memory_id = f"mem_{uuid.uuid4().hex[:8]}"
    memory = {
        "id": memory_id,
        "content": content,
        "category": category,
        "importance": max(0.0, min(1.0, importance)),
        "created_at": datetime.now().isoformat(),
    }

    relationship["shared_memories"].append(memory)
    relationship["updated_at"] = datetime.now()

    return memory


@router.delete("/{relationship_id}/memories/{memory_id}")
async def delete_shared_memory(
    relationship_id: str,
    memory_id: str,
) -> dict[str, str]:
    """Delete a shared memory.

    Args:
        relationship_id: Relationship ID.
        memory_id: Memory ID.

    Returns:
        Deletion confirmation.

    Raises:
        HTTPException: If relationship or memory not found.
    """
    state = get_app_state()

    if relationship_id not in state.relationships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relationship {relationship_id} not found",
        )

    relationship = state.relationships[relationship_id]
    memories = relationship.get("shared_memories", [])

    # Find and remove memory
    original_len = len(memories)
    relationship["shared_memories"] = [m for m in memories if m.get("id") != memory_id]

    if len(relationship["shared_memories"]) == original_len:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory {memory_id} not found",
        )

    relationship["updated_at"] = datetime.now()

    return {"status": "deleted", "memory_id": memory_id}


__all__ = ["router"]
