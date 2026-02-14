"""Tests for the shared API helper functions.

Covers:
- Successful requests (GET, POST, PATCH, DELETE)
- Narrowed exception handling (URLError, TimeoutError, JSONDecodeError)
- Retry with exponential back-off for transient failures
- Non-retryable errors fail immediately
"""

from __future__ import annotations

import json
import urllib.error
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def app_context():
    """Provide a Flask application context for API helper tests."""
    from personaut.server.ui.app import create_ui_app

    flask_app = create_ui_app(api_base_url="http://test-api:8000/api")
    flask_app.config["TESTING"] = True
    with flask_app.app_context():
        yield flask_app


def _mock_response(body: bytes | str = b'{"ok":true}', status: int = 200) -> MagicMock:
    """Create a mock urllib response context-manager."""
    if isinstance(body, str):
        body = body.encode()
    resp = MagicMock()
    resp.read.return_value = body
    resp.status = status
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ═══════════════════════════════════════════════════════════════════════════
# Basic happy-path tests
# ═══════════════════════════════════════════════════════════════════════════


class TestApiGet:
    def test_successful_get(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        with patch("urllib.request.urlopen", return_value=_mock_response()):
            assert api_get("/test") == {"ok": True}

    def test_uses_correct_base_url(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
            api_get("/individuals")
            req = mock_open.call_args[0][0]
            assert req.full_url == "http://test-api:8000/api/individuals"


class TestApiPost:
    def test_successful_post(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_post

        with patch("urllib.request.urlopen", return_value=_mock_response('{"id":"new_123"}')) as mock_open:
            result = api_post("/individuals", {"name": "Test"})
        assert result == {"id": "new_123"}
        req = mock_open.call_args[0][0]
        assert req.method == "POST"
        assert json.loads(req.data)["name"] == "Test"


class TestApiPatch:
    def test_successful_patch(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_patch

        with patch("urllib.request.urlopen", return_value=_mock_response('{"updated":true}')) as mock_open:
            result = api_patch("/individuals/123", {"name": "Updated"})
        assert result == {"updated": True}
        req = mock_open.call_args[0][0]
        assert req.method == "PATCH"


class TestApiDelete:
    def test_successful_delete(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_delete

        with patch("urllib.request.urlopen", return_value=_mock_response(status=204)):
            assert api_delete("/individuals/123") is True

    def test_non_204_returns_false(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_delete

        with patch("urllib.request.urlopen", return_value=_mock_response(status=200)):
            assert api_delete("/individuals/123") is False


# ═══════════════════════════════════════════════════════════════════════════
# Narrowed exception types
# ═══════════════════════════════════════════════════════════════════════════


class TestNarrowedExceptions:
    """Verify that only expected exception types are caught."""

    def test_url_error_returns_none(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("DNS failed")):
            assert api_get("/test") is None

    def test_timeout_error_returns_none(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            assert api_get("/test") is None

    def test_json_decode_error_returns_none(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        resp = _mock_response(b"not json at all")
        resp.read.return_value = b"not json at all"
        # json.loads will raise JSONDecodeError
        with patch("urllib.request.urlopen", return_value=resp):
            assert api_get("/test") is None

    def test_os_error_returns_none(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        with patch("urllib.request.urlopen", side_effect=ConnectionResetError("reset")):
            assert api_get("/test") is None

    def test_http_404_returns_none(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        exc = urllib.error.HTTPError(
            "http://test/api/x",
            404,
            "Not Found",
            {},
            BytesIO(b""),
        )
        with patch("urllib.request.urlopen", side_effect=exc):
            assert api_get("/x") is None

    def test_delete_url_error_returns_false(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_delete

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
            assert api_delete("/x") is False

    def test_post_timeout_returns_none(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_post

        with patch("urllib.request.urlopen", side_effect=TimeoutError("slow")):
            assert api_post("/x", {"a": 1}) is None

    def test_patch_os_error_returns_none(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_patch

        with patch("urllib.request.urlopen", side_effect=BrokenPipeError("pipe")):
            assert api_patch("/x", {"a": 1}) is None


# ═══════════════════════════════════════════════════════════════════════════
# Retry behaviour
# ═══════════════════════════════════════════════════════════════════════════


class TestRetryBehaviour:
    """Verify exponential back-off retry on transient errors."""

    def test_retries_on_503_then_succeeds(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        exc_503 = urllib.error.HTTPError(
            "http://test/api/x",
            503,
            "Service Unavailable",
            {},
            BytesIO(b""),
        )
        with (
            patch("urllib.request.urlopen", side_effect=[exc_503, _mock_response()]) as mock_open,
            patch("personaut.server.ui.views.api_helpers.time.sleep") as mock_sleep,
        ):
            result = api_get("/x")

        assert result == {"ok": True}
        assert mock_open.call_count == 2
        # First retry delay = 0.3 * 2^0 = 0.3
        mock_sleep.assert_called_once()
        assert 0.2 <= mock_sleep.call_args[0][0] <= 0.4

    def test_retries_on_429_then_succeeds(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_post

        exc_429 = urllib.error.HTTPError(
            "http://test/api/x",
            429,
            "Too Many Requests",
            {},
            BytesIO(b""),
        )
        with (
            patch("urllib.request.urlopen", side_effect=[exc_429, _mock_response('{"created":true}')]) as mock_open,
            patch("personaut.server.ui.views.api_helpers.time.sleep"),
        ):
            result = api_post("/x", {"data": 1})

        assert result == {"created": True}
        assert mock_open.call_count == 2

    def test_no_retry_on_404(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        exc_404 = urllib.error.HTTPError(
            "http://test/api/x",
            404,
            "Not Found",
            {},
            BytesIO(b""),
        )
        with (
            patch("urllib.request.urlopen", side_effect=exc_404) as mock_open,
            patch("personaut.server.ui.views.api_helpers.time.sleep") as mock_sleep,
        ):
            result = api_get("/x")

        assert result is None
        assert mock_open.call_count == 1  # No retries
        mock_sleep.assert_not_called()

    def test_no_retry_on_400(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_post

        exc_400 = urllib.error.HTTPError(
            "http://test/api/x",
            400,
            "Bad Request",
            {},
            BytesIO(b""),
        )
        with (
            patch("urllib.request.urlopen", side_effect=exc_400) as mock_open,
            patch("personaut.server.ui.views.api_helpers.time.sleep") as mock_sleep,
        ):
            result = api_post("/x", {"bad": "data"})

        assert result is None
        assert mock_open.call_count == 1
        mock_sleep.assert_not_called()

    def test_retries_on_url_error_then_gives_up(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        exc = urllib.error.URLError("Connection refused")
        with (
            patch("urllib.request.urlopen", side_effect=exc) as mock_open,
            patch("personaut.server.ui.views.api_helpers.time.sleep") as mock_sleep,
        ):
            result = api_get("/x")

        assert result is None
        # 1 initial + 2 retries = 3 total
        assert mock_open.call_count == 3
        assert mock_sleep.call_count == 2

    def test_retries_on_timeout_error(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_delete

        with (
            patch("urllib.request.urlopen", side_effect=TimeoutError("slow")) as mock_open,
            patch("personaut.server.ui.views.api_helpers.time.sleep"),
        ):
            result = api_delete("/x")

        assert result is False
        assert mock_open.call_count == 3  # 1 + 2 retries

    def test_exponential_backoff_delays(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_get

        exc = urllib.error.URLError("Connection refused")
        with (
            patch("urllib.request.urlopen", side_effect=exc),
            patch("personaut.server.ui.views.api_helpers.time.sleep") as mock_sleep,
        ):
            api_get("/x")

        # Delays: 0.3 * 2^0 = 0.3, 0.3 * 2^1 = 0.6
        delays = [c[0][0] for c in mock_sleep.call_args_list]
        assert len(delays) == 2
        assert abs(delays[0] - 0.3) < 0.01
        assert abs(delays[1] - 0.6) < 0.01

    def test_retry_delete_on_502(self, app_context) -> None:
        from personaut.server.ui.views.api_helpers import api_delete

        exc_502 = urllib.error.HTTPError(
            "http://test/api/x",
            502,
            "Bad Gateway",
            {},
            BytesIO(b""),
        )
        with (
            patch("urllib.request.urlopen", side_effect=[exc_502, _mock_response(status=204)]) as mock_open,
            patch("personaut.server.ui.views.api_helpers.time.sleep"),
        ):
            result = api_delete("/x")

        assert result is True
        assert mock_open.call_count == 2
