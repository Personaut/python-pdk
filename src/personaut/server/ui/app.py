"""Flask Web UI application for Personaut.

This module provides the Flask application for the web-based
persona interaction interface.

Example:
    >>> from personaut.server.ui.app import create_ui_app
    >>> app = create_ui_app()
    >>> app.run(port=5000)
"""

from __future__ import annotations

import os
import secrets
from typing import Any


def create_ui_app(
    api_base_url: str = "http://localhost:8000/api",
    template_folder: str | None = None,
    static_folder: str | None = None,
) -> Any:
    """Create and configure the Flask UI application.

    Args:
        api_base_url: Base URL of the API server.
        template_folder: Custom template folder path.
        static_folder: Custom static folder path.

    Returns:
        Configured Flask application.

    Raises:
        ImportError: If Flask is not installed.

    Example:
        >>> app = create_ui_app(api_base_url="http://localhost:8000/api")
    """
    try:
        from flask import Flask, jsonify
    except ImportError as e:
        msg = "Flask not installed. Install with: pip install personaut[server]"
        raise ImportError(msg) from e

    from pathlib import Path

    # Use default paths if not provided
    if template_folder is None:
        template_folder = str(Path(__file__).parent / "templates")
    if static_folder is None:
        static_folder = str(Path(__file__).parent / "static")

    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
    )

    app.config["API_BASE_URL"] = api_base_url
    app.config["SECRET_KEY"] = os.environ.get("PERSONAUT_SECRET_KEY", secrets.token_hex(32))

    # Register blueprints
    _register_blueprints(app)

    # ── Serve generated data (portraits, videos) from the data dir ───
    @app.route("/data/<path:filepath>")
    def serve_data(filepath: str) -> Any:
        """Serve portrait and video files from the data directory."""
        from flask import abort, send_from_directory
        from pathlib import Path

        # Only allow portraits/ and videos/ subdirectories
        if not filepath.startswith(("portraits/", "videos/")):
            abort(404)

        storage_path = os.environ.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db")
        data_dir = str(Path(storage_path).resolve().parent)
        return send_from_directory(data_dir, filepath)

    # Health check
    @app.route("/health")
    def health() -> Any:
        """Health check endpoint."""
        return jsonify({"status": "healthy", "ui": True})

    return app


def _register_blueprints(app: Any) -> None:
    """Register view blueprints.

    Args:
        app: Flask application instance.
    """
    from personaut.server.ui.views.chat import bp as chat_bp
    from personaut.server.ui.views.dashboard import bp as dashboard_bp
    from personaut.server.ui.views.individuals import bp as individuals_bp
    from personaut.server.ui.views.relationships import bp as relationships_bp
    from personaut.server.ui.views.simulations import bp as simulations_bp
    from personaut.server.ui.views.situations import bp as situations_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(individuals_bp)
    app.register_blueprint(situations_bp)
    app.register_blueprint(relationships_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(simulations_bp)


__all__ = ["create_ui_app"]
