"""WebSocket routes for real-time updates.

This module provides WebSocket endpoints for real-time message
broadcasting and state change notifications.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections.

    This class tracks all active connections and provides methods
    for broadcasting messages to connected clients.

    Attributes:
        active_connections: Dict mapping session IDs to WebSocket connections.
        subscriptions: Dict mapping topics to sets of WebSocket connections.

    Example:
        >>> manager = ConnectionManager()
        >>> await manager.connect(websocket, "session_123")
        >>> await manager.broadcast({"type": "message", "content": "Hello"})
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.subscriptions: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
    ) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection.
            session_id: Session ID to associate with this connection.
        """
        await websocket.accept()
        async with self._lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []
            self.active_connections[session_id].append(websocket)

    async def disconnect(
        self,
        websocket: WebSocket,
        session_id: str,
    ) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove.
            session_id: Session ID associated with this connection.
        """
        async with self._lock:
            if session_id in self.active_connections:
                if websocket in self.active_connections[session_id]:
                    self.active_connections[session_id].remove(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]

            # Remove from all subscriptions
            for connections in self.subscriptions.values():
                connections.discard(websocket)

    async def subscribe(
        self,
        websocket: WebSocket,
        topic: str,
    ) -> None:
        """Subscribe a connection to a topic.

        Args:
            websocket: The WebSocket connection.
            topic: Topic to subscribe to.
        """
        async with self._lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(websocket)

    async def unsubscribe(
        self,
        websocket: WebSocket,
        topic: str,
    ) -> None:
        """Unsubscribe a connection from a topic.

        Args:
            websocket: The WebSocket connection.
            topic: Topic to unsubscribe from.
        """
        async with self._lock:
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(websocket)

    async def send_to_session(
        self,
        session_id: str,
        message: dict[str, Any],
    ) -> None:
        """Send a message to all connections in a session.

        Args:
            session_id: Session ID to send to.
            message: Message to send.
        """
        connections = self.active_connections.get(session_id, [])
        disconnected: list[WebSocket] = []

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected
        for conn in disconnected:
            await self.disconnect(conn, session_id)

    async def broadcast(
        self,
        message: dict[str, Any],
    ) -> None:
        """Broadcast a message to all active connections.

        Args:
            message: Message to broadcast.
        """
        for session_id, connections in list(self.active_connections.items()):
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    await self.disconnect(connection, session_id)

    async def publish(
        self,
        topic: str,
        message: dict[str, Any],
    ) -> None:
        """Publish a message to all subscribers of a topic.

        Args:
            topic: Topic to publish to.
            message: Message to publish.
        """
        connections = self.subscriptions.get(topic, set())
        disconnected: list[tuple[WebSocket, str]] = []

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Find the session for this connection
                for sid, conns in self.active_connections.items():
                    if connection in conns:
                        disconnected.append((connection, sid))
                        break

        # Clean up disconnected
        for conn, sid in disconnected:
            await self.disconnect(conn, sid)

    def get_connection_count(self) -> int:
        """Get total number of active connections.

        Returns:
            Total connection count.
        """
        return sum(len(conns) for conns in self.active_connections.values())

    def get_session_connections(self, session_id: str) -> int:
        """Get number of connections for a session.

        Args:
            session_id: Session ID.

        Returns:
            Connection count for the session.
        """
        return len(self.active_connections.get(session_id, []))


# Global connection manager instance
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager.

    Returns:
        The ConnectionManager instance.
    """
    return manager


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
) -> None:
    """WebSocket endpoint for a chat session.

    Args:
        websocket: The WebSocket connection.
        session_id: Session ID to connect to.
    """
    await manager.connect(websocket, session_id)

    try:
        # Send connection confirmation
        await websocket.send_json(
            {
                "type": "connected",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, session_id, message)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Invalid JSON",
                    }
                )

    except WebSocketDisconnect:
        await manager.disconnect(websocket, session_id)
        # Notify other connections in session
        await manager.send_to_session(
            session_id,
            {
                "type": "user_disconnected",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            },
        )


async def handle_websocket_message(
    websocket: WebSocket,
    session_id: str,
    message: dict[str, Any],
) -> None:
    """Handle incoming WebSocket message.

    Args:
        websocket: The WebSocket connection.
        session_id: Session ID.
        message: Parsed message dict.
    """
    msg_type = message.get("type", "")

    if msg_type == "ping":
        await websocket.send_json({"type": "pong"})

    elif msg_type == "subscribe":
        topic = message.get("topic", "")
        if topic:
            await manager.subscribe(websocket, topic)
            await websocket.send_json(
                {
                    "type": "subscribed",
                    "topic": topic,
                }
            )

    elif msg_type == "unsubscribe":
        topic = message.get("topic", "")
        if topic:
            await manager.unsubscribe(websocket, topic)
            await websocket.send_json(
                {
                    "type": "unsubscribed",
                    "topic": topic,
                }
            )

    elif msg_type == "message":
        # Broadcast message to session
        content = message.get("content", "")
        sender = message.get("sender", "Anonymous")

        await manager.send_to_session(
            session_id,
            {
                "type": "message",
                "content": content,
                "sender": sender,
                "timestamp": datetime.now().isoformat(),
            },
        )

    else:
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Unknown message type: {msg_type}",
            }
        )


# ============================================================================
# Notification Functions
# ============================================================================


async def notify_emotional_state_change(
    individual_id: str,
    old_state: dict[str, float],
    new_state: dict[str, float],
) -> None:
    """Broadcast emotional state change notification.

    Args:
        individual_id: Individual whose state changed.
        old_state: Previous emotional state.
        new_state: New emotional state.
    """
    await manager.publish(
        f"individual:{individual_id}",
        {
            "type": "emotional_state_change",
            "individual_id": individual_id,
            "old_state": old_state,
            "new_state": new_state,
            "timestamp": datetime.now().isoformat(),
        },
    )


async def notify_trigger_activation(
    individual_id: str,
    trigger_id: str,
    trigger_name: str,
    effects: dict[str, Any],
) -> None:
    """Broadcast trigger activation notification.

    Args:
        individual_id: Individual whose trigger activated.
        trigger_id: ID of the activated trigger.
        trigger_name: Name of the trigger.
        effects: Effects of the trigger.
    """
    await manager.publish(
        f"individual:{individual_id}",
        {
            "type": "trigger_activated",
            "individual_id": individual_id,
            "trigger_id": trigger_id,
            "trigger_name": trigger_name,
            "effects": effects,
            "timestamp": datetime.now().isoformat(),
        },
    )


async def notify_new_message(
    session_id: str,
    message_id: str,
    sender_id: str | None,
    sender_name: str,
    content: str,
) -> None:
    """Broadcast new message notification.

    Args:
        session_id: Session ID.
        message_id: Message ID.
        sender_id: Sender's individual ID (or None for human).
        sender_name: Sender's display name.
        content: Message content.
    """
    await manager.send_to_session(
        session_id,
        {
            "type": "new_message",
            "message_id": message_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        },
    )


async def notify_session_ended(
    session_id: str,
    reason: str = "ended",
) -> None:
    """Broadcast session ended notification.

    Args:
        session_id: Session ID.
        reason: Reason for ending.
    """
    await manager.send_to_session(
        session_id,
        {
            "type": "session_ended",
            "session_id": session_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        },
    )


__all__ = [
    "ConnectionManager",
    "get_connection_manager",
    "manager",
    "notify_emotional_state_change",
    "notify_new_message",
    "notify_session_ended",
    "notify_trigger_activation",
    "router",
]
