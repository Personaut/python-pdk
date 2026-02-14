"""Tests for base simulation."""

from __future__ import annotations

import json
import tempfile
from typing import Any

import pytest

from personaut.simulations.simulation import (
    SimulationResult,
    create_simulation,
)
from personaut.simulations.styles import SimulationStyle
from personaut.simulations.types import SimulationType
from tests.personaut.simulations.conftest import MockIndividual, MockSituation


class TestSimulationResult:
    """Tests for SimulationResult dataclass."""

    def test_create_result(self) -> None:
        """Test creating a simulation result."""
        result = SimulationResult(
            simulation_id="test_001",
            simulation_type=SimulationType.CONVERSATION,
            content="Test content",
        )
        assert result.simulation_id == "test_001"
        assert result.simulation_type == SimulationType.CONVERSATION
        assert result.content == "Test content"

    def test_result_to_dict(self) -> None:
        """Test converting result to dictionary."""
        result = SimulationResult(
            simulation_id="test_001",
            simulation_type=SimulationType.SURVEY,
            content="Test content",
            metadata={"key": "value"},
        )
        data = result.to_dict()
        assert data["simulation_id"] == "test_001"
        assert data["simulation_type"] == "survey"
        assert data["content"] == "Test content"
        assert data["metadata"]["key"] == "value"
        assert "created_at" in data

    def test_result_to_json(self) -> None:
        """Test converting result to JSON."""
        result = SimulationResult(
            simulation_id="test_001",
            simulation_type=SimulationType.CONVERSATION,
            content="Test content",
        )
        json_str = result.to_json()
        data = json.loads(json_str)
        assert data["simulation_id"] == "test_001"


class TestCreateSimulation:
    """Tests for create_simulation factory function."""

    def test_create_conversation_simulation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test creating a conversation simulation."""
        simulation = create_simulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            type=SimulationType.CONVERSATION,
        )
        assert simulation.simulation_type == SimulationType.CONVERSATION

    def test_create_survey_simulation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test creating a survey simulation."""
        simulation = create_simulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            type=SimulationType.SURVEY,
        )
        assert simulation.simulation_type == SimulationType.SURVEY

    def test_create_outcome_simulation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test creating an outcome simulation."""
        simulation = create_simulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            type=SimulationType.OUTCOME_SUMMARY,
        )
        assert simulation.simulation_type == SimulationType.OUTCOME_SUMMARY

    def test_create_live_simulation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test creating a live simulation."""
        simulation = create_simulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            type=SimulationType.LIVE_CONVERSATION,
        )
        assert simulation.simulation_type == SimulationType.LIVE_CONVERSATION

    def test_create_with_string_type(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test creating simulation with string type."""
        simulation = create_simulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            type="conversation",
        )
        assert simulation.simulation_type == SimulationType.CONVERSATION

    def test_create_with_style(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test creating simulation with explicit style."""
        simulation = create_simulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            type=SimulationType.CONVERSATION,
            style=SimulationStyle.JSON,
        )
        assert simulation.style == SimulationStyle.JSON

    def test_create_with_invalid_type_raises(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test creating with invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid simulation type"):
            create_simulation(
                situation=mock_situation,
                individuals=[mock_individual_sarah],
                type="invalid_type",
            )


class TestSimulationRun:
    """Tests for simulation run functionality."""

    def test_run_creates_output_files(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test run creates output files."""
        simulation = create_simulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            type=SimulationType.CONVERSATION,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            results = simulation.run(num=2, dir=tmpdir)
            assert len(results) == 2

            for result in results:
                assert result.output_path is not None
                assert result.output_path.exists()

    def test_run_returns_results(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test run returns SimulationResult objects."""
        simulation = create_simulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            type=SimulationType.SURVEY,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            results = simulation.run(num=1, dir=tmpdir)
            assert len(results) == 1
            assert isinstance(results[0], SimulationResult)
            assert results[0].content


class TestSimulationAgeRestriction:
    """Tests for age restriction enforcement at the simulation level."""

    def test_run_rejects_underage_individual_object(
        self,
        mock_situation: MockSituation,
    ) -> None:
        """Simulation.run() rejects individuals with age < 18 (object attribute)."""
        from personaut.types.exceptions import AgeRestrictionError

        underage = MockIndividual(name="Minor")
        underage.age = 15  # type: ignore[attr-defined]

        simulation = create_simulation(
            situation=mock_situation,
            individuals=[underage],
            type=SimulationType.CONVERSATION,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(AgeRestrictionError, match="at least 18"):
                simulation.run(num=1, dir=tmpdir)

    def test_run_rejects_underage_dict_individual(
        self,
        mock_situation: MockSituation,
    ) -> None:
        """Simulation.run() rejects dict individuals with age < 18."""
        from personaut.types.exceptions import AgeRestrictionError

        underage_dict: dict[str, Any] = {"name": "Child", "age": 10}

        simulation = create_simulation(
            situation=mock_situation,
            individuals=[underage_dict],
            type=SimulationType.CONVERSATION,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(AgeRestrictionError, match="at least 18"):
                simulation.run(num=1, dir=tmpdir)

    def test_run_allows_adult_individual(
        self,
        mock_situation: MockSituation,
    ) -> None:
        """Simulation.run() allows individuals aged 18+."""
        adult = MockIndividual(name="Adult")
        adult.age = 25  # type: ignore[attr-defined]

        simulation = create_simulation(
            situation=mock_situation,
            individuals=[adult],
            type=SimulationType.CONVERSATION,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            results = simulation.run(num=1, dir=tmpdir)
            assert len(results) == 1
