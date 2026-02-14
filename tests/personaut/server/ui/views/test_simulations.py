"""Tests for the simulations view routes."""

from __future__ import annotations

from unittest.mock import patch


class TestSimulationsIndex:
    """Tests for GET /simulations/."""

    def test_index_returns_200(self, client) -> None:
        resp = client.get("/simulations/")
        assert resp.status_code == 200

    def test_index_lists_individuals(self, client) -> None:
        resp = client.get("/simulations/")
        html = resp.data.decode()
        assert "Sarah Chen" in html


class TestSimulationsRun:
    """Tests for POST /simulations/run."""

    def test_run_no_individuals_returns_400(self, client) -> None:
        resp = client.post(
            "/simulations/run",
            json={
                "mode": "conversation",
                "individual_ids": [],
                "situation_id": "sit_test_001",
            },
        )
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_run_unknown_mode_returns_400(self, client) -> None:
        resp = client.post(
            "/simulations/run",
            json={
                "mode": "unknown_mode",
                "individual_ids": ["ind_test_001"],
                "situation_id": "sit_test_001",
            },
        )
        assert resp.status_code == 400

    def test_run_conversation_needs_two_individuals(self, client) -> None:
        """Conversation mode requires at least 2 individuals."""
        with patch(
            "personaut.server.ui.views.simulation_engine.get_llm",
            return_value=None,
        ):
            resp = client.post(
                "/simulations/run",
                json={
                    "mode": "conversation",
                    "individual_ids": ["ind_test_001"],
                    "situation_id": "sit_test_001",
                },
            )
        assert resp.status_code == 400
        assert "2 individuals" in resp.get_json()["error"]

    def test_run_conversation_success(self, client, mock_router) -> None:
        """Conversation with 2 individuals should produce turns."""
        with patch(
            "personaut.server.ui.views.simulation_engine.get_llm",
            return_value=None,
        ):
            resp = client.post(
                "/simulations/run",
                json={
                    "mode": "conversation",
                    "individual_ids": ["ind_test_001", "ind_test_002"],
                    "situation_id": "sit_test_001",
                    "max_turns": 2,
                    "variations": 1,
                },
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["mode"] == "conversation"
        assert data["turn_count"] == 2
        assert len(data["variations"]) == 1
        # Should have turns in the variation
        turns = data["variations"][0]["turns"]
        assert len(turns) == 2

    def test_run_survey_no_questions_returns_400(self, client) -> None:
        """Survey mode without questions should fail."""
        with patch(
            "personaut.server.ui.views.simulation_engine.get_llm",
            return_value=None,
        ):
            resp = client.post(
                "/simulations/run",
                json={
                    "mode": "survey",
                    "individual_ids": ["ind_test_001"],
                    "situation_id": "sit_test_001",
                    "questions": [],
                },
            )
        assert resp.status_code == 400

    def test_run_survey_success(self, client) -> None:
        """Survey with questions should return respondent answers."""
        with patch(
            "personaut.server.ui.views.simulation_engine.get_llm",
            return_value=None,
        ):
            resp = client.post(
                "/simulations/run",
                json={
                    "mode": "survey",
                    "individual_ids": ["ind_test_001"],
                    "situation_id": "sit_test_001",
                    "questions": [
                        {"text": "How do you feel?", "type": "open_ended"},
                    ],
                    "variations": 1,
                },
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["mode"] == "survey"
        assert data["question_count"] == 1
        assert data["respondent_count"] == 1
        respondents = data["variations"][0]["respondents"]
        assert respondents[0]["name"] == "Sarah Chen"

    def test_run_outcome_no_description_returns_400(self, client) -> None:
        """Outcome tracking without outcome description should fail."""
        with patch(
            "personaut.server.ui.views.simulation_engine.get_llm",
            return_value=None,
        ):
            resp = client.post(
                "/simulations/run",
                json={
                    "mode": "outcome",
                    "individual_ids": ["ind_test_001"],
                    "situation_id": "sit_test_001",
                    "outcome": "",
                },
            )
        assert resp.status_code == 400

    def test_run_outcome_success(self, client) -> None:
        """Outcome tracking should produce trials with correlations."""
        with patch(
            "personaut.server.ui.views.simulation_engine.get_llm",
            return_value=None,
        ):
            resp = client.post(
                "/simulations/run",
                json={
                    "mode": "outcome",
                    "individual_ids": ["ind_test_001"],
                    "situation_id": "sit_test_001",
                    "outcome": "Customer agrees to purchase",
                    "num_trials": 2,
                    "max_turns": 2,
                    "vary_by": "traits",
                },
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["mode"] == "outcome"
        assert data["total_trials"] == 2
        assert len(data["trials"]) == 2
        # Each trial should have a conversation and an outcome
        for trial in data["trials"]:
            assert "conversation" in trial
            assert "outcome" in trial

    def test_run_with_default_situation(self, client, mock_router) -> None:
        """Should create a default situation when none is provided."""
        # Remove the situation from the router so it returns None
        mock_router.get_routes.pop("/situations/sit_test_001", None)
        with patch(
            "personaut.server.ui.views.simulation_engine.get_llm",
            return_value=None,
        ):
            resp = client.post(
                "/simulations/run",
                json={
                    "mode": "conversation",
                    "individual_ids": ["ind_test_001", "ind_test_002"],
                    "max_turns": 1,
                },
            )
        assert resp.status_code == 200
