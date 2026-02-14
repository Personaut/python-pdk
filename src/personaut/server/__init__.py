"""Server package for Personaut.

This package provides the live interaction server with REST API
and web UI for managing personas and running simulations.

Example:
    >>> from personaut.server import LiveInteractionServer
    >>> server = LiveInteractionServer()
    >>> server.start(api_port=8000, ui_port=5000)
"""

from __future__ import annotations

from personaut.server.server import LiveInteractionClient, LiveInteractionServer


__all__ = [
    "LiveInteractionClient",
    "LiveInteractionServer",
]
