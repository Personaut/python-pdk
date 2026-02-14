"""FastAPI application for the Personaut API.

This module provides the main FastAPI application with CORS configuration,
exception handlers, and documentation.

Example:
    >>> from personaut.server.api.app import create_app
    >>> app = create_app()
    >>> # Run with: uvicorn personaut.server.api.app:app
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from personaut.server.api.schemas import ErrorResponse, ValidationErrorResponse
from personaut.types.exceptions import (
    PersonautError,
    TrustThresholdError,
    ValidationError,
)


if TYPE_CHECKING:
    from collections.abc import AsyncIterator


# ============================================================================
# Application State
# ============================================================================


class AppState:
    """Container for application-wide state."""

    def __init__(self) -> None:
        """Initialize application state."""
        self.individuals: dict[str, Any] = {}
        self.situations: dict[str, Any] = {}
        self.relationships: dict[str, Any] = {}
        self.sessions: dict[str, Any] = {}
        self.storage: Any = None
        self.persistence: Any = None  # Persistence layer (SQLite adapter)


_app_state: AppState | None = None


def get_app_state() -> AppState:
    """Get the application state.

    Returns:
        The application state instance.

    Raises:
        RuntimeError: If application state not initialized.
    """
    if _app_state is None:
        msg = "Application state not initialized"
        raise RuntimeError(msg)
    return _app_state


# ============================================================================
# Lifespan Management
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan.

    Args:
        app: The FastAPI application.

    Yields:
        None during application runtime.
    """
    import logging

    log = logging.getLogger(__name__)

    global _app_state
    _app_state = AppState()

    # ── Read storage config from environment ─────────────────────────
    import os

    storage_type = os.environ.get("PERSONAUT_STORAGE_TYPE", "sqlite").lower().strip()
    storage_path = os.environ.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db").strip()

    # ── Initialise persistence ──────────────────────────────────────
    if storage_type == "memory":
        log.info("Storage type is 'memory' – running without disk persistence")
    else:
        try:
            from personaut.server.api.persistence import Persistence

            db_path = Path(storage_path).resolve()
            db_path.parent.mkdir(parents=True, exist_ok=True)

            persist = Persistence(db_path)
            _app_state.persistence = persist
            log.info("Persistence enabled: %s (type=%s)", db_path, storage_type)

            # Hydrate in-memory state from DB ─────────────────────────
            for ind in persist.load_individuals():
                _app_state.individuals[ind["id"]] = ind
                # Hydrate memories from the dedicated memories table
                memories = persist.load_memories(ind["id"])
                if memories:
                    ind["memories"] = memories
            log.info("Loaded %d individuals from DB", len(_app_state.individuals))

            for sit in persist.load_situations():
                _app_state.situations[sit["id"]] = sit
            log.info("Loaded %d situations from DB", len(_app_state.situations))

            for rel in persist.load_relationships():
                _app_state.relationships[rel["id"]] = rel
            log.info("Loaded %d relationships from DB", len(_app_state.relationships))

            for sess in persist.load_sessions():
                _app_state.sessions[sess["id"]] = sess
            log.info("Loaded %d sessions from DB", len(_app_state.sessions))

        except Exception:
            log.exception("Failed to initialise persistence – running in-memory only")

    yield

    # ── Shutdown ────────────────────────────────────────────────────
    if _app_state and _app_state.persistence:
        try:
            _app_state.persistence.close()
        except Exception:
            log.exception("Error closing persistence")
    _app_state = None


# ============================================================================
# Exception Handlers
# ============================================================================


async def personaut_error_handler(
    request: Request,
    exc: PersonautError,
) -> JSONResponse:
    """Handle PersonautError exceptions.

    Args:
        request: The request that caused the error.
        exc: The exception.

    Returns:
        JSON error response.
    """
    error_response = ErrorResponse(
        error=type(exc).__name__,
        message=str(exc),
        details=getattr(exc, "details", None),
    )
    status_code = status.HTTP_400_BAD_REQUEST

    # Map specific errors to HTTP status codes
    if isinstance(exc, TrustThresholdError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(),
    )


async def validation_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: The request that caused the error.
        exc: The exception.

    Returns:
        JSON error response.
    """
    # Handle FastAPI/Pydantic validation errors
    errors = []
    if hasattr(exc, "errors"):
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", ""),
                    "value": error.get("input"),
                }
            )

    response = ValidationErrorResponse(errors=errors)  # type: ignore[arg-type]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(),
    )


async def generic_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected errors.

    Args:
        request: The request that caused the error.
        exc: The exception.

    Returns:
        JSON error response.
    """
    error_response = ErrorResponse(
        error="InternalServerError",
        message="An unexpected error occurred",
        details={"type": type(exc).__name__},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


# ============================================================================
# Application Factory
# ============================================================================


def create_app(
    title: str = "Personaut API",
    version: str = "0.1.0",
    debug: bool = False,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        title: API title for documentation.
        version: API version.
        debug: Enable debug mode.
        cors_origins: Allowed CORS origins.

    Returns:
        Configured FastAPI application.

    Example:
        >>> app = create_app(debug=True)
        >>> # Add to uvicorn or other ASGI server
    """
    app = FastAPI(
        title=title,
        version=version,
        description=("Personaut API for managing simulated individuals, emotional states, and live interactions."),
        debug=debug,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Configure CORS
    origins = cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    app.add_exception_handler(PersonautError, personaut_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_error_handler)

    # Register routes
    _register_routes(app)

    # ── Serve generated data (portraits, videos) from the data dir ───
    @app.get("/data/{filepath:path}", tags=["data"])
    async def serve_data(filepath: str) -> Any:
        """Serve portrait and video files from the data directory."""
        import os

        from fastapi.responses import FileResponse

        # Only allow portraits/ and videos/ subdirectories
        if not filepath.startswith(("portraits/", "videos/")):
            raise HTTPException(status_code=404, detail="Not found")

        storage_path = os.environ.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db")
        data_dir = Path(storage_path).resolve().parent
        candidate = data_dir / filepath

        if not candidate.exists() or not candidate.is_file():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(str(candidate))

    return app


def _register_routes(app: FastAPI) -> None:
    """Register API routes.

    Args:
        app: The FastAPI application.
    """
    from personaut.server.api.routes import (
        emotions,
        individuals,
        masks,
        memories,
        relationships,
        sessions,
        situations,
        triggers,
        websocket,
    )

    # Include routers with prefixes
    app.include_router(individuals.router, prefix="/api/individuals", tags=["individuals"])
    app.include_router(emotions.router, tags=["emotions"])
    app.include_router(memories.router, tags=["memories"])
    app.include_router(masks.router, tags=["masks"])
    app.include_router(triggers.router, tags=["triggers"])
    app.include_router(situations.router, prefix="/api/situations", tags=["situations"])
    app.include_router(relationships.router, prefix="/api/relationships", tags=["relationships"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(websocket.router, prefix="/api", tags=["websocket"])

    # Health check endpoint
    @app.get("/api/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """Check API health."""
        return {"status": "healthy", "version": app.version}


# Create default application instance
app = create_app()


__all__ = [
    "AppState",
    "app",
    "create_app",
    "get_app_state",
]
