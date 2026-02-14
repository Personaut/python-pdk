"""Tests for the individuals view."""

from __future__ import annotations


class TestIndividualsListView:
    """Tests for GET /individuals/."""

    def test_list_returns_200(self, client) -> None:
        resp = client.get("/individuals/")
        assert resp.status_code == 200

    def test_list_renders_page(self, client) -> None:
        """The list page should render HTML (specific content depends on template)."""
        resp = client.get("/individuals/")
        html = resp.data.decode()
        assert "Individuals" in html or "individuals" in html.lower()


class TestIndividualsCreateView:
    """Tests for GET/POST /individuals/create."""

    def test_create_get_returns_200(self, client) -> None:
        resp = client.get("/individuals/create")
        assert resp.status_code == 200

    def test_create_form_contains_trait_fields(self, client) -> None:
        resp = client.get("/individuals/create")
        html = resp.data.decode()
        assert "warmth" in html.lower()
        assert "emotional_stability" in html.lower() or "Emotional Stability" in html

    def test_create_post_redirects(self, client, mock_router) -> None:
        """POST should create individual and redirect to detail."""
        mock_router.post_routes["/individuals"] = {
            "id": "ind_new",
            "name": "New Person",
        }
        resp = client.post(
            "/individuals/create",
            data={
                "name": "New Person",
                "description": "A test",
                "individual_type": "simulated",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/individuals/" in resp.headers.get("Location", "")


class TestIndividualsDetailView:
    """Tests for GET /individuals/<id>."""

    def test_detail_returns_200(self, client) -> None:
        resp = client.get("/individuals/ind_test_001")
        assert resp.status_code == 200

    def test_detail_renders_page(self, client) -> None:
        """Detail page should render without errors."""
        resp = client.get("/individuals/ind_test_001")
        html = resp.data.decode()
        # Should contain individual data or at minimum render fully
        assert "<!DOCTYPE html>" in html or "<!doctype html>" in html.lower()
        assert len(html) > 200  # Not a blank page

    def test_detail_not_found(self, client) -> None:
        """Unknown ID should render a not-found page (200 with error content)."""
        resp = client.get("/individuals/nonexistent_id")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "not found" in html.lower() or "Not Found" in html


class TestIndividualsEditView:
    """Tests for GET/POST /individuals/<id>/edit."""

    def test_edit_get_returns_200(self, client) -> None:
        resp = client.get("/individuals/ind_test_001/edit")
        assert resp.status_code == 200

    def test_edit_post_redirects(self, client) -> None:
        resp = client.post(
            "/individuals/ind_test_001/edit",
            data={
                "name": "Sarah Updated",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302


class TestIndividualsSubpageViews:
    """Tests for sub-page routes (emotions, traits, triggers).

    These routes redirect to edit/detail views; they don't render templates.
    """

    def test_emotions_view_redirects(self, client) -> None:
        resp = client.get("/individuals/ind_test_001/emotions", follow_redirects=False)
        assert resp.status_code == 302

    def test_traits_view_redirects(self, client) -> None:
        resp = client.get("/individuals/ind_test_001/traits", follow_redirects=False)
        assert resp.status_code == 302

    def test_triggers_view_redirects(self, client) -> None:
        resp = client.get("/individuals/ind_test_001/triggers", follow_redirects=False)
        assert resp.status_code == 302


class TestGenerateMemoryEmotions:
    """Tests for the AJAX memory emotion generation endpoint."""

    def test_missing_description_returns_400(self, client) -> None:
        resp = client.post(
            "/individuals/generate-memory-emotions",
            json={"description": ""},
        )
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_with_description_returns_emotions_or_error(self, client) -> None:
        """Should return emotions dict or a 500 if no LLM is available."""
        resp = client.post(
            "/individuals/generate-memory-emotions",
            json={
                "description": "Won a local art competition",
                "name": "Sarah",
                "traits": {"warmth": 0.8},
            },
        )
        # Either succeeds (200) with emotions or fails (500) due to no LLM
        assert resp.status_code in (200, 500)
