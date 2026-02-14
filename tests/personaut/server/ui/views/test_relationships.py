"""Tests for the relationships view."""

from __future__ import annotations


class TestRelationshipsListView:
    def test_list_returns_200(self, client) -> None:
        resp = client.get("/relationships/")
        assert resp.status_code == 200


class TestRelationshipsCreateView:
    def test_create_get_returns_200(self, client) -> None:
        resp = client.get("/relationships/create")
        assert resp.status_code == 200

    def test_create_post_redirects(self, client) -> None:
        resp = client.post("/relationships/create", data={}, follow_redirects=False)
        assert resp.status_code == 302


class TestRelationshipsDetailView:
    def test_detail_returns_200(self, client) -> None:
        resp = client.get("/relationships/rel_test_001")
        assert resp.status_code == 200


class TestRelationshipsEditView:
    def test_edit_get_returns_200(self, client) -> None:
        resp = client.get("/relationships/rel_test_001/edit")
        assert resp.status_code == 200

    def test_edit_post_redirects(self, client) -> None:
        resp = client.post("/relationships/rel_test_001/edit", data={}, follow_redirects=False)
        assert resp.status_code == 302
