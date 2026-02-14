"""Memory management API routes.

Provides CRUD endpoints for individual memories, plus text-based search.
Memories are stored as dicts in the individual's dict under a 'memories'
key, consistent with the dict-based storage pattern used across the API.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from personaut.server.api.app import get_app_state
from personaut.server.api.schemas import (
    MemoryCreate,
    MemoryListResponse,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
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


def _ensure_memories_list(ind: dict[str, Any]) -> list[dict[str, Any]]:
    """Ensure the individual dict has a 'memories' list."""
    if "memories" not in ind or not isinstance(ind.get("memories"), list):
        ind["memories"] = []
    memories: list[dict[str, Any]] = ind["memories"]
    return memories


def _memory_dict_to_response(mem: dict[str, Any], owner_id: str) -> MemoryResponse:
    """Convert a memory dict to a MemoryResponse schema."""
    return MemoryResponse(
        id=mem.get("id", ""),
        description=mem.get("description", ""),
        owner_id=owner_id,
        salience=mem.get("salience", 0.5),
        memory_type=mem.get("memory_type", "individual"),
        emotional_state=mem.get("emotional_state"),
        metadata=mem.get("metadata"),
    )


# ---------------------------------------------------------------------------
# Endpoints  (mounted at /api/individuals/{individual_id}/memories)
# ---------------------------------------------------------------------------


@router.get(
    "/api/individuals/{individual_id}/memories",
    response_model=MemoryListResponse,
    summary="List memories for an individual",
)
async def list_memories(individual_id: str) -> MemoryListResponse:
    """Return all memories belonging to this individual."""
    ind = _get_individual(individual_id)
    memories = _ensure_memories_list(ind)

    return MemoryListResponse(
        memories=[_memory_dict_to_response(m, individual_id) for m in memories],
        total=len(memories),
    )


@router.post(
    "/api/individuals/{individual_id}/memories",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a memory to an individual",
)
async def create_memory(
    individual_id: str,
    body: MemoryCreate,
) -> MemoryResponse:
    """Create a new memory and attach it to the individual."""
    ind = _get_individual(individual_id)
    memories = _ensure_memories_list(ind)

    memory_id = f"mem_{uuid.uuid4().hex[:8]}"
    memory: dict[str, Any] = {
        "id": memory_id,
        "description": body.description,
        "owner_id": individual_id,
        "salience": body.salience,
        "memory_type": "individual",
        "emotional_state": body.emotional_state,
        "metadata": body.metadata or {},
    }

    memories.append(memory)

    # Persist to DB if available
    state = get_app_state()
    if state.persistence is not None:
        try:
            state.persistence.save_memory(individual_id, memory)
        except Exception:
            logger.warning("Failed to persist memory %s to DB", memory_id, exc_info=True)

    logger.info(
        "Created memory %s for %s: %s (salience=%.2f)",
        memory_id,
        individual_id,
        body.description[:60],
        body.salience,
    )
    return _memory_dict_to_response(memory, individual_id)


@router.get(
    "/api/individuals/{individual_id}/memories/{memory_id}",
    response_model=MemoryResponse,
    summary="Get a specific memory",
)
async def get_memory(individual_id: str, memory_id: str) -> MemoryResponse:
    """Retrieve a single memory by ID."""
    ind = _get_individual(individual_id)
    memories = _ensure_memories_list(ind)

    for m in memories:
        if m.get("id") == memory_id:
            return _memory_dict_to_response(m, individual_id)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Memory {memory_id} not found",
    )


@router.delete(
    "/api/individuals/{individual_id}/memories/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a memory",
)
async def delete_memory(individual_id: str, memory_id: str) -> None:
    """Remove a memory from the individual."""
    ind = _get_individual(individual_id)
    memories = _ensure_memories_list(ind)

    original_count = len(memories)
    ind["memories"] = [m for m in memories if m.get("id") != memory_id]

    if len(ind["memories"]) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory {memory_id} not found",
        )

    logger.info("Deleted memory %s from %s", memory_id, individual_id)


@router.post(
    "/api/individuals/{individual_id}/memories/search",
    response_model=MemorySearchResponse,
    summary="Search memories by text query",
)
async def search_memories(
    individual_id: str,
    body: MemorySearchRequest,
) -> MemorySearchResponse:
    """Simple keyword search across an individual's memories.

    Searches the description field for substring matches
    (case-insensitive). For vector-based semantic search,
    use the PDK's search_memories() with an embedding function.
    """
    ind = _get_individual(individual_id)
    memories = _ensure_memories_list(ind)

    query_lower = body.query.lower()
    matched = []
    for m in memories:
        desc = m.get("description", "")
        meta_str = str(m.get("metadata", {}))
        if query_lower in desc.lower() or query_lower in meta_str.lower():
            matched.append(m)

    matched = matched[: body.limit]

    return MemorySearchResponse(
        query=body.query,
        results=[_memory_dict_to_response(m, individual_id) for m in matched],
        total=len(matched),
    )
