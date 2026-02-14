"""Individual management API routes.

This module provides CRUD endpoints for managing individuals.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from personaut.server.api.app import get_app_state
from personaut.server.api.schemas import (
    IndividualCreate,
    IndividualListResponse,
    IndividualResponse,
    IndividualUpdate,
)


router = APIRouter()


@router.get("", response_model=IndividualListResponse)
async def list_individuals(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
) -> IndividualListResponse:
    """List all individuals.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        List of individuals with pagination.
    """
    state = get_app_state()
    # Filter out non-individual entries (e.g. emotion_history_* lists)
    # that are stored in the same dict
    all_individuals = [v for v in state.individuals.values() if isinstance(v, dict) and "id" in v]

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_individuals[start:end]

    return IndividualListResponse(
        individuals=[IndividualResponse(**ind) for ind in paginated],
        total=len(all_individuals),
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=IndividualResponse, status_code=status.HTTP_201_CREATED)
async def create_individual(
    data: IndividualCreate,
) -> IndividualResponse:
    """Create a new individual.

    Args:
        data: Individual creation data.

    Returns:
        Created individual.
    """
    state = get_app_state()

    # Generate unique ID
    individual_id = f"ind_{uuid.uuid4().hex[:8]}"

    # Build individual data
    now = datetime.now()
    individual: dict[str, Any] = {
        "id": individual_id,
        "name": data.name,
        "description": data.description,
        "age": data.age,
        "individual_type": data.individual_type,
        "emotional_state": data.initial_emotions or {},
        "trait_profile": data.initial_traits or {},
        "physical_features": data.physical_features or {},
        "portrait_url": None,
        "metadata": data.metadata or {},
        "created_at": now,
        "updated_at": None,
    }

    # Auto-generate portrait if requested and physical features are present
    if data.generate_portrait and data.physical_features:
        try:
            from personaut.images.portrait import generate_portrait, save_portrait
            from personaut.individuals.physical import PhysicalFeatures

            features = PhysicalFeatures.from_dict(data.physical_features)
            image_bytes = generate_portrait(features, name=data.name)
            if image_bytes:
                portrait_url = save_portrait(image_bytes, individual_id)
                individual["portrait_url"] = portrait_url
        except Exception as e:
            import logging

            logging.getLogger(__name__).error("Portrait generation failed for %s: %s", data.name, e)

    # Store
    state.individuals[individual_id] = individual

    # Persist to SQLite
    if state.persistence:
        try:
            state.persistence.save_individual(individual)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist individual %s",
                individual_id,
            )

    return IndividualResponse(**individual)


@router.get("/{individual_id}", response_model=IndividualResponse)
async def get_individual(
    individual_id: str,
) -> IndividualResponse:
    """Get individual by ID.

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

    return IndividualResponse(**state.individuals[individual_id])


@router.patch("/{individual_id}", response_model=IndividualResponse)
async def update_individual(
    individual_id: str,
    data: IndividualUpdate,
) -> IndividualResponse:
    """Update individual by ID.

    Args:
        individual_id: Individual ID.
        data: Update data.

    Returns:
        Updated individual.

    Raises:
        HTTPException: If individual not found.
    """
    state = get_app_state()

    if individual_id not in state.individuals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Individual {individual_id} not found",
        )

    individual = state.individuals[individual_id]

    # Update fields
    if data.name is not None:
        individual["name"] = data.name
    if data.description is not None:
        individual["description"] = data.description
    if data.physical_features is not None:
        individual["physical_features"] = data.physical_features
    if data.metadata is not None:
        individual["metadata"] = data.metadata

    individual["updated_at"] = datetime.now()

    # Persist update
    if state.persistence:
        try:
            state.persistence.save_individual(individual)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist individual update %s",
                individual_id,
            )

    return IndividualResponse(**individual)


@router.delete("/{individual_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_individual(
    individual_id: str,
) -> None:
    """Delete individual by ID.

    Args:
        individual_id: Individual ID.

    Raises:
        HTTPException: If individual not found.
    """
    state = get_app_state()

    if individual_id not in state.individuals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Individual {individual_id} not found",
        )

    del state.individuals[individual_id]

    # Persist delete
    if state.persistence:
        try:
            state.persistence.delete_individual(individual_id)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist individual delete %s",
                individual_id,
            )


@router.post(
    "/{individual_id}/portrait",
    response_model=IndividualResponse,
)
async def generate_individual_portrait(
    individual_id: str,
) -> IndividualResponse:
    """Generate or regenerate a portrait for an individual.

    Uses the individual's physical features to generate a portrait
    image via the Gemini image generation model.

    Args:
        individual_id: Individual ID.

    Returns:
        Updated individual with portrait_url.

    Raises:
        HTTPException: If individual not found or generation fails.
    """
    state = get_app_state()

    if individual_id not in state.individuals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Individual {individual_id} not found",
        )

    individual = state.individuals[individual_id]
    physical_features = individual.get("physical_features", {})

    if not physical_features:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Individual has no physical features — add them first",
        )

    try:
        from personaut.images.portrait import generate_portrait, save_portrait
        from personaut.individuals.physical import PhysicalFeatures

        features = PhysicalFeatures.from_dict(physical_features)
        image_bytes = generate_portrait(features, name=individual.get("name", ""))

        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Image generation returned no data. Check your GOOGLE_API_KEY.",
            )

        portrait_url = save_portrait(image_bytes, individual_id)
        individual["portrait_url"] = portrait_url
        individual["updated_at"] = datetime.now()

        # Persist portrait_url
        if state.persistence:
            try:
                state.persistence.save_individual(individual)
            except Exception:
                logging.getLogger(__name__).exception(
                    "Failed to persist portrait update for %s",
                    individual_id,
                )

        return IndividualResponse(**individual)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portrait generation failed: {e}",
        ) from e


__all__ = ["router"]
