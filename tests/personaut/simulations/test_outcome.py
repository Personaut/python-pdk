"""Tests for outcome simulation."""

from __future__ import annotations

import json
import tempfile

from personaut.simulations.outcome import OutcomeSimulation
from personaut.simulations.styles import SimulationStyle
from personaut.simulations.types import SimulationType
from tests.personaut.simulations.conftest import MockIndividual, MockSituation


class TestOutcomeSimulation:
    """Tests for OutcomeSimulation class."""

    def test_create_outcome_simulation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test creating an outcome simulation."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            target_outcome="Customer accepts offer",
        )
        assert simulation.simulation_type == SimulationType.OUTCOME_SUMMARY
        assert simulation.target_outcome == "Customer accepts offer"

    def test_default_style_is_narrative(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test default style is narrative."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
        )
        assert simulation.style == SimulationStyle.NARRATIVE

    def test_generate_outcome_analysis(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test generating outcome analysis."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            target_outcome="Positive interaction",
        )
        content = simulation._generate()

        # Should contain outcome analysis elements
        assert "=== Outcome Analysis ===" in content
        assert "Target Outcome:" in content
        assert "Result:" in content or "Likelihood:" in content

    def test_json_format(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test JSON format output."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            style=SimulationStyle.JSON,
            target_outcome="Success",
        )
        content = simulation._generate()

        data = json.loads(content)
        assert data["simulation_type"] == "outcome_summary"
        assert data["target_outcome"] == "Success"
        assert "outcome_achieved" in data
        assert "analysis" in data

    def test_factor_analysis(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
        mock_individual_mike: MockIndividual,
    ) -> None:
        """Test factor analysis is included."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah, mock_individual_mike],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            style=SimulationStyle.JSON,
            target_outcome="Collaboration",
        )
        content = simulation._generate()
        data = json.loads(content)

        analysis = data.get("analysis", {})
        factors = analysis.get("factors", {})

        # Should have emotional and trait factors for each participant
        assert any("emotional" in k for k in factors.keys())

    def test_insights_generation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test insights are generated."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            style=SimulationStyle.JSON,
            target_outcome="Success",
        )
        content = simulation._generate()
        data = json.loads(content)

        analysis = data.get("analysis", {})
        insights = analysis.get("key_insights", [])
        assert isinstance(insights, list)

    def test_recommendations_generation(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test recommendations are generated."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            style=SimulationStyle.JSON,
            target_outcome="Success",
        )
        content = simulation._generate()
        data = json.loads(content)

        analysis = data.get("analysis", {})
        recommendations = analysis.get("recommendations", [])
        assert isinstance(recommendations, list)


class TestMultipleRuns:
    """Tests for running multiple outcome simulations."""

    def test_run_multiple_simulations(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test running multiple simulations."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            target_outcome="Success",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            results = simulation.run(num=5, dir=tmpdir)
            assert len(results) == 5

            # All results should have output paths
            for result in results:
                assert result.output_path is not None
                assert result.output_path.exists()

    def test_summary_file_created(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test summary file is created for multiple runs."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            target_outcome="Success",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            from pathlib import Path

            simulation.run(num=5, dir=tmpdir)

            summary_path = Path(tmpdir) / "outcome_summary.txt"
            assert summary_path.exists()

            content = summary_path.read_text()
            assert "Total Simulations: 5" in content


class TestRandomization:
    """Tests for outcome randomization features."""

    def test_randomize_emotions(
        self,
        mock_situation: MockSituation,
        mock_individual_sarah: MockIndividual,
    ) -> None:
        """Test emotion randomization."""
        simulation = OutcomeSimulation(
            situation=mock_situation,
            individuals=[mock_individual_sarah],
            simulation_type=SimulationType.OUTCOME_SUMMARY,
            target_outcome="Success",
            randomize_emotions=["anxious", "hopeful"],
            randomize_range=(0.3, 0.7),
        )

        # Just verify it runs without error
        content = simulation._generate()
        assert content
