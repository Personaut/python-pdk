"""Shared API helper functions for Flask UI views.

Provides a thin HTTP client layer for communicating with the FastAPI
backend from Flask view functions.  All helpers read the base URL from
``current_app.config["API_BASE_URL"]`` so they work correctly regardless
of how the server is configured.

Features:
- Narrowed exception handling (``URLError``, ``JSONDecodeError``,
  ``TimeoutError``, ``OSError``) instead of bare ``Exception``.
- Automatic retry with exponential back-off for transient failures.

Example::

    from personaut.server.ui.views.api_helpers import api_get, api_post

    data = api_get("/individuals")
    result = api_post("/individuals", {"name": "Sarah"})
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

from flask import current_app


logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://localhost:8000/api"

# ── Retry configuration ─────────────────────────────────────────────────
MAX_RETRIES: int = 2
"""Maximum number of retries for transient failures (0 = no retries)."""

RETRY_BACKOFF_BASE: float = 0.3
"""Base delay in seconds; actual delay = base * 2^attempt."""

#: Transient HTTP status codes that warrant a retry.
_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 502, 503, 504})

#: Exception types considered transient (network-level).
_RETRYABLE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    urllib.error.URLError,
    TimeoutError,
    OSError,  # covers ConnectionError, BrokenPipeError, etc.
)

#: All "expected" exception types — anything outside this is truly unexpected
#: and will propagate rather than being silently swallowed.
_EXPECTED_EXCEPTIONS: tuple[type[BaseException], ...] = (
    urllib.error.URLError,  # DNS, connection refused, HTTP errors
    urllib.error.HTTPError,  # subclass of URLError, 4xx/5xx
    json.JSONDecodeError,  # malformed response body
    TimeoutError,  # socket/connection timeout
    OSError,  # low-level socket errors
    ValueError,  # edge-case JSON issues
)


def _base_url() -> str:
    """Return the API base URL from Flask config."""
    return str(current_app.config.get("API_BASE_URL", _DEFAULT_BASE_URL))


def _is_retryable(exc: BaseException) -> bool:
    """Decide whether an exception warrants a retry."""
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in _RETRYABLE_STATUS_CODES
    return isinstance(exc, _RETRYABLE_EXCEPTIONS)


# ═══════════════════════════════════════════════════════════════════════════
# Public helpers
# ═══════════════════════════════════════════════════════════════════════════


def api_get(path: str, *, timeout: int = 5) -> Any:
    """Fetch JSON from the API server via GET.

    Args:
        path: API path (e.g. ``"/individuals"``).
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response, or ``None`` on any expected error.
    """
    url = f"{_base_url()}{path}"
    last_exc: BaseException | None = None

    for attempt in range(1 + MAX_RETRIES):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except _EXPECTED_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < MAX_RETRIES and _is_retryable(exc):
                delay = RETRY_BACKOFF_BASE * (2**attempt)
                logger.debug(
                    "api_get %s attempt %d failed (%s), retrying in %.1fs",
                    path,
                    attempt + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)
                continue
            break

    logger.debug("api_get %s failed: %s", path, last_exc, exc_info=True)
    return None


def api_post(path: str, data: dict[str, Any], *, timeout: int = 5) -> Any:
    """Send a POST request with JSON body to the API server.

    Args:
        path: API path.
        data: Dictionary to JSON-encode as the request body.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response, or ``None`` on any expected error.
    """
    url = f"{_base_url()}{path}"
    body = json.dumps(data).encode()
    last_exc: BaseException | None = None

    for attempt in range(1 + MAX_RETRIES):
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except _EXPECTED_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < MAX_RETRIES and _is_retryable(exc):
                delay = RETRY_BACKOFF_BASE * (2**attempt)
                logger.debug(
                    "api_post %s attempt %d failed (%s), retrying in %.1fs",
                    path,
                    attempt + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)
                continue
            break

    logger.debug("api_post %s failed: %s", path, last_exc, exc_info=True)
    return None


def api_patch(path: str, data: dict[str, Any], *, timeout: int = 5) -> Any:
    """Send a PATCH request with JSON body to the API server.

    Args:
        path: API path.
        data: Dictionary to JSON-encode as the request body.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON response, or ``None`` on any expected error.
    """
    url = f"{_base_url()}{path}"
    body = json.dumps(data).encode()
    last_exc: BaseException | None = None

    for attempt in range(1 + MAX_RETRIES):
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="PATCH",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except _EXPECTED_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < MAX_RETRIES and _is_retryable(exc):
                delay = RETRY_BACKOFF_BASE * (2**attempt)
                logger.debug(
                    "api_patch %s attempt %d failed (%s), retrying in %.1fs",
                    path,
                    attempt + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)
                continue
            break

    logger.debug("api_patch %s failed: %s", path, last_exc, exc_info=True)
    return None


def api_delete(path: str, *, timeout: int = 5) -> bool:
    """Send a DELETE request to the API server.

    Args:
        path: API path.
        timeout: Request timeout in seconds.

    Returns:
        ``True`` if the server returned 204 No Content, ``False`` otherwise.
    """
    url = f"{_base_url()}{path}"
    last_exc: BaseException | None = None

    for attempt in range(1 + MAX_RETRIES):
        try:
            req = urllib.request.Request(url, method="DELETE")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return bool(resp.status == 204)
        except _EXPECTED_EXCEPTIONS as exc:
            last_exc = exc
            if attempt < MAX_RETRIES and _is_retryable(exc):
                delay = RETRY_BACKOFF_BASE * (2**attempt)
                logger.debug(
                    "api_delete %s attempt %d failed (%s), retrying in %.1fs",
                    path,
                    attempt + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)
                continue
            break

    logger.debug("api_delete %s failed: %s", path, last_exc, exc_info=True)
    return False


__all__ = [
    "MAX_RETRIES",
    "RETRY_BACKOFF_BASE",
    "api_delete",
    "api_get",
    "api_patch",
    "api_post",
]
