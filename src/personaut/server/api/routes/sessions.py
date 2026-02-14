"""Session management API routes.

This module provides endpoints for managing chat sessions and messages.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from personaut.server.api.app import get_app_state
from personaut.server.api.schemas import (
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    SessionCreate,
    SessionListResponse,
    SessionResponse,
)


router = APIRouter()


def _get_session_or_404(session_id: str) -> dict[str, Any]:
    """Get session or raise 404."""
    state = get_app_state()
    if session_id not in state.sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    result: dict[str, Any] = state.sessions[session_id]
    return result


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


@router.get("", response_model=SessionListResponse)
async def list_sessions() -> SessionListResponse:
    """List all sessions.

    Returns:
        List of sessions.
    """
    state = get_app_state()
    all_sessions = list(state.sessions.values())

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s["id"],
                situation_id=s["situation_id"],
                individual_ids=s["individual_ids"],
                human_id=s.get("human_id"),
                active=s.get("active", True),
                message_count=len(s.get("messages", [])),
                metadata=s.get("metadata"),
                created_at=s.get("created_at", datetime.now()),
                updated_at=s.get("updated_at"),
            )
            for s in all_sessions
        ],
        total=len(all_sessions),
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
) -> SessionResponse:
    """Create a new chat session.

    Args:
        data: Session creation data.

    Returns:
        Created session.
    """
    state = get_app_state()

    # Validate situation exists
    if data.situation_id not in state.situations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Situation {data.situation_id} not found",
        )

    # Validate individuals exist
    for ind_id in data.individual_ids:
        _get_individual_or_404(ind_id)

    # Remember what Uncle Ben said: "With great power comes great
    # responsibility." Don't be a creep!
    from personaut.types.exceptions import MINIMUM_SIMULATION_AGE

    for ind_id in data.individual_ids:
        individual = state.individuals[ind_id]
        ind_age = individual.get("age")
        if ind_age is not None and ind_age < MINIMUM_SIMULATION_AGE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Individual '{individual.get('name', ind_id)}' is under "
                    f"{MINIMUM_SIMULATION_AGE}. All simulated personas must "
                    f"represent adults."
                ),
            )

    # Generate unique ID
    session_id = f"sess_{uuid.uuid4().hex[:8]}"

    # Build session data
    now = datetime.now()
    session: dict[str, Any] = {
        "id": session_id,
        "situation_id": data.situation_id,
        "individual_ids": data.individual_ids,
        "human_id": data.human_id,
        "active": True,
        "messages": [],
        "metadata": data.metadata or {},
        "created_at": now,
        "updated_at": None,
    }

    # Store
    state.sessions[session_id] = session

    # Persist
    if state.persistence:
        try:
            state.persistence.save_session(session)
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Failed to persist session %s",
                session_id,
            )

    return SessionResponse(
        id=session_id,
        situation_id=data.situation_id,
        individual_ids=data.individual_ids,
        human_id=data.human_id,
        active=True,
        message_count=0,
        metadata=data.metadata,
        created_at=now,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
) -> SessionResponse:
    """Get session by ID.

    Args:
        session_id: Session ID.

    Returns:
        Session data.
    """
    session = _get_session_or_404(session_id)

    return SessionResponse(
        id=session["id"],
        situation_id=session["situation_id"],
        individual_ids=session["individual_ids"],
        human_id=session.get("human_id"),
        active=session.get("active", True),
        message_count=len(session.get("messages", [])),
        metadata=session.get("metadata"),
        created_at=session.get("created_at", datetime.now()),
        updated_at=session.get("updated_at"),
    )


@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    data: MessageCreate,
) -> MessageResponse:
    """Send a message in a session.

    Args:
        session_id: Session ID.
        data: Message data.

    Returns:
        Created message with AI response.
    """
    session = _get_session_or_404(session_id)

    if not session.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active",
        )

    state = get_app_state()

    # Generate message ID
    message_id = f"msg_{uuid.uuid4().hex[:8]}"
    now = datetime.now()

    # Determine sender name
    sender_name = "Human"
    emotional_state = None
    if data.sender_id:
        individual = _get_individual_or_404(data.sender_id)
        sender_name = individual.get("name", "Unknown")
        emotional_state = individual.get("emotional_state")

    # Create message
    message: dict[str, Any] = {
        "id": message_id,
        "session_id": session_id,
        "sender_id": data.sender_id,
        "sender_name": sender_name,
        "content": data.content,
        "action": data.action,
        "timestamp": now,
        "emotional_state": emotional_state,
    }

    # Add to session
    session["messages"].append(message)
    session["updated_at"] = now

    # Persist message + session update
    if state.persistence:
        try:
            state.persistence.save_message(session_id, message)
            state.persistence.save_session(session)
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist message %s",
                message_id,
            )

    return MessageResponse(**message)


@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def get_messages(
    session_id: str,
) -> MessageListResponse:
    """Get all messages in a session.

    Args:
        session_id: Session ID.

    Returns:
        List of messages.
    """
    session = _get_session_or_404(session_id)
    messages = session.get("messages", [])

    return MessageListResponse(
        messages=[MessageResponse(**msg) for msg in messages],
        total=len(messages),
        session_id=session_id,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(
    session_id: str,
) -> None:
    """End (deactivate) a session.

    Args:
        session_id: Session ID.
    """
    session = _get_session_or_404(session_id)
    session["active"] = False
    session["updated_at"] = datetime.now()

    # Persist
    state = get_app_state()
    if state.persistence:
        try:
            state.persistence.save_session(session)
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Failed to persist session end %s",
                session_id,
            )


import logging


logger = logging.getLogger(__name__)


@router.post("/{session_id}/video")
async def generate_session_video(
    session_id: str,
) -> dict[str, Any]:
    """Generate a POV video of the conversation using Veo.

    Args:
        session_id: Session ID.

    Returns:
        Dict with video_url pointing to the generated MP4.
    """
    session = _get_session_or_404(session_id)
    state = get_app_state()

    messages = session.get("messages", [])
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no messages to generate video from",
        )

    # Require a real conversation — must have messages from both
    # the human and the character (not just one-sided)
    has_human = any(m.get("sender_name") == "Human" for m in messages)
    has_character = any(m.get("sender_name") != "Human" for m in messages)
    if not (has_human and has_character):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Video requires a real conversation with messages from "
                "both you and the character. Chat with them first!"
            ),
        )

    # Get individual info for physical description + portrait
    individual_name = "Unknown"
    physical_description = ""
    portrait_path = None

    ind_ids = session.get("individual_ids", [])
    if ind_ids:
        ind_id = ind_ids[0]
        individual = state.individuals.get(ind_id, {})
        individual_name = individual.get("name", "Unknown")

        # Build physical description string
        phys = individual.get("physical_features") or {}
        if phys:
            parts = []
            for key in [
                "age_appearance",
                "height",
                "build",
                "hair",
                "eyes",
                "skin_tone",
                "facial_features",
                "distinguishing_features",
                "accessories",
                "clothing_style",
            ]:
                val = phys.get(key)
                if val:
                    parts.append(f"{key.replace('_', ' ')}: {val}")
            physical_description = "; ".join(parts)

        # Check for portrait
        portrait_url = individual.get("portrait_url", "")
        if portrait_url:
            from pathlib import Path

            storage_path = os.environ.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db")
            data_root = Path(storage_path).resolve().parent
            # /data/portraits/xxx.png -> portraits/xxx.png
            rel = portrait_url.lstrip("/")
            if rel.startswith("data/"):
                rel = rel[len("data/") :]
            elif rel.startswith("static/"):
                # Legacy URLs — look in data dir anyway
                rel = rel[len("static/") :]
            candidate = data_root / rel
            if candidate.exists():
                portrait_path = str(candidate)

    # Format messages for the video generator
    formatted = []
    for msg in messages:
        role = "user" if msg.get("sender_name") == "Human" else "assistant"
        formatted.append({"role": role, "content": msg.get("content", "")})

    try:
        from personaut.images.video import generate_conversation_video

        video_url = generate_conversation_video(
            messages=formatted,
            individual_name=individual_name,
            physical_description=physical_description,
            portrait_path=portrait_path,
            session_id=session_id,
        )

        if not video_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Video generation returned no output",
            )

        # Store video_url on the session
        session["video_url"] = video_url
        session["updated_at"] = datetime.now()

        # Persist video_url
        if state.persistence:
            try:
                state.persistence.save_session(session)
            except Exception:
                logger.exception(
                    "Failed to persist video_url for session %s",
                    session_id,
                )

        return {
            "video_url": video_url,
            "session_id": session_id,
            "individual_name": individual_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Video generation failed for session %s: %s", session_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video generation failed: {e}",
        ) from e


__all__ = ["router"]
