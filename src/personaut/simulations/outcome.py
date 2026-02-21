"""Outcome simulation for Personaut PDK.

This module provides the OutcomeSimulation class for analyzing
whether target outcomes are likely to be achieved.

Example:
    >>> from personaut.simulations.outcome import OutcomeSimulation
    >>> simulation = OutcomeSimulation(
    ...     situation=sales_situation,
    ...     individuals=[customer, sales_rep],
    ...     simulation_type=SimulationType.OUTCOME_SUMMARY,
    ...     target_outcome="Customer accepts upgrade offer",
    ... )
    >>> results = simulation.run(num=10, dir="./")
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from personaut.simulations.simulation import Simulation
from personaut.simulations.styles import SimulationStyle


@dataclass
class OutcomeSimulation(Simulation):
    """Simulation for outcome analysis and prediction.

    Analyzes the likelihood of achieving a target outcome based on
    participant emotional states, traits, and situational factors.

    Attributes:
        target_outcome: Description of the desired outcome.
        randomize: List of attributes to randomize between runs.
        randomize_emotions: Specific emotions to randomize.
        randomize_range: Min/max range for randomization.
        randomize_traits: Traits to randomize.

    Example:
        >>> simulation = OutcomeSimulation(
        ...     situation=situation,
        ...     individuals=[customer, sales_rep],
        ...     simulation_type=SimulationType.OUTCOME_SUMMARY,
        ...     target_outcome="Customer accepts upgrade",
        ... )
    """

    target_outcome: str = ""
    randomize: list[Any] = field(default_factory=list)
    randomize_emotions: list[str] = field(default_factory=list)
    randomize_range: tuple[float, float] = (0.2, 0.8)
    randomize_traits: list[str] = field(default_factory=list)

    # Internal tracking
    _run_results: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def _generate(self, run_index: int = 0, **options: Any) -> str:
        """Generate outcome analysis.

        Args:
            run_index: Index of this run (0-based).
            **options: Additional options.

        Returns:
            Formatted outcome analysis.
        """
        # Apply randomization if this is a batch run
        if options.get("apply_randomization", True):
            self._apply_randomization()

        # Analyze outcome likelihood
        outcome_achieved, analysis = self._analyze_outcome()

        # Record this run's result
        run_result = {
            "run_index": run_index,
            "outcome_achieved": outcome_achieved,
            "analysis": analysis,
            "participant_states": self._capture_participant_states(),
        }
        self._run_results.append(run_result)

        # Format output
        return self._format_outcome(run_result)

    def run(
        self,
        num: int = 1,
        dir: str | Path = "./",
        **options: Any,
    ) -> list[Any]:
        """Run the simulation with aggregate statistics.

        Args:
            num: Number of simulation variations.
            dir: Output directory.
            **options: Additional options.

        Returns:
            List of SimulationResult objects.
        """
        # Reset run results
        self._run_results = []

        # Run individual simulations
        results = super().run(num=num, dir=dir, **options)

        # If multiple runs, add aggregate summary
        if num > 1:
            summary = self._generate_summary()
            summary_content = self._format_summary(summary)

            # Save summary file
            from pathlib import Path

            summary_path = Path(dir) / "outcome_summary.txt"
            summary_path.write_text(summary_content, encoding="utf-8")

        return results

    def _apply_randomization(self) -> None:
        """Apply randomization to specified attributes."""
        min_val, max_val = self.randomize_range

        # Randomize emotional states
        for individual in self.individuals:
            emotional_state = self._get_emotional_state(individual)

            if emotional_state is None:
                continue

            # Randomize specific emotions
            for emotion in self.randomize_emotions:
                if hasattr(emotional_state, "change_emotion"):
                    value = random.uniform(min_val, max_val)
                    emotional_state.change_emotion(emotion, value)
                elif isinstance(emotional_state, dict):
                    emotional_state[emotion] = random.uniform(min_val, max_val)

    def _analyze_outcome(self) -> tuple[bool, dict[str, Any]]:
        """Analyze whether the target outcome is likely to be achieved.

        Returns:
            Tuple of (outcome_achieved, analysis_details).
        """
        # Calculate likelihood based on various factors
        factors: dict[str, float] = {}

        # Analyze each participant's contribution
        for individual in self.individuals:
            name = self._get_individual_name(individual)
            emotional_state = self._get_emotional_state(individual)
            traits = self._get_traits(individual)

            # Emotional factor
            emotional_score = self._calculate_emotional_factor(emotional_state)
            factors[f"{name}_emotional"] = emotional_score

            # Trait factor
            trait_score = self._calculate_trait_factor(traits)
            factors[f"{name}_traits"] = trait_score

        # Situation factor
        situation_score = self._calculate_situation_factor()
        factors["situation"] = situation_score

        # Calculate overall likelihood
        total_score = sum(factors.values()) / len(factors) if factors else 0.5

        # Add some randomness to reflect natural variability
        noise = random.gauss(0, 0.1)
        final_probability = max(0.0, min(1.0, total_score + noise))

        # Determine outcome
        outcome_achieved = random.random() < final_probability

        analysis = {
            "likelihood": final_probability,
            "factors": factors,
            "key_insights": self._generate_insights(factors),
            "recommendations": self._generate_recommendations(factors),
        }

        return outcome_achieved, analysis

    def _calculate_emotional_factor(self, emotional_state: Any) -> float:
        """Calculate how emotional state affects outcome likelihood.

        Args:
            emotional_state: Individual's emotional state.

        Returns:
            Score from 0 to 1.
        """
        if emotional_state is None:
            return 0.5

        # Positive emotions generally improve outcomes
        positive_emotions = {
            "trusting",
            "content",
            "satisfied",
            "hopeful",
            "cheerful",
            "excited",
            "proud",
            "appreciated",
            "respected",
            "loving",
        }
        negative_emotions = {
            "anxious",
            "angry",
            "hostile",
            "insecure",
            "depressed",
            "hurt",
            "rejected",
            "hateful",
            "helpless",
            "critical",
        }

        emotions = {}
        if hasattr(emotional_state, "to_dict"):
            emotions = emotional_state.to_dict()
        elif isinstance(emotional_state, dict):
            emotions = emotional_state

        positive_score = sum(emotions.get(e, 0) for e in positive_emotions)
        negative_score = sum(emotions.get(e, 0) for e in negative_emotions)

        # Normalize
        total = positive_score + negative_score
        if total == 0:
            return 0.5

        return float(0.3 + 0.4 * (positive_score / total))

    def _calculate_trait_factor(self, traits: Any) -> float:
        """Calculate how traits affect outcome likelihood.

        Args:
            traits: Individual's trait profile.

        Returns:
            Score from 0 to 1.
        """
        if traits is None:
            return 0.5

        # Get trait values
        trait_dict = {}
        if hasattr(traits, "to_dict"):
            trait_dict = traits.to_dict()
        elif hasattr(traits, "get_trait"):
            # Try common traits
            for trait_name in ["warmth", "openness", "agreeableness"]:
                value = traits.get_trait(trait_name)
                if value is not None:
                    trait_dict[trait_name] = value
        elif isinstance(traits, dict):
            trait_dict = traits

        if not trait_dict:
            return 0.5

        # Calculate average of positive traits
        positive_traits = ["warmth", "openness", "agreeableness", "extraversion"]
        values = [trait_dict.get(t, 0.5) for t in positive_traits if t in trait_dict]

        if not values:
            return 0.5

        return float(0.3 + 0.4 * (sum(values) / len(values)))

    def _calculate_situation_factor(self) -> float:
        """Calculate how the situation affects outcome likelihood.

        Returns:
            Score from 0 to 1.
        """
        # Look for situation context clues
        description = getattr(self.situation, "description", "").lower()

        # Positive context indicators
        positive_indicators = [
            "friendly",
            "comfortable",
            "relaxed",
            "casual",
            "welcoming",
            "positive",
            "successful",
            "good",
            "pleasant",
        ]
        negative_indicators = [
            "tense",
            "awkward",
            "hostile",
            "difficult",
            "challenging",
            "stressful",
            "negative",
            "problematic",
        ]

        positive_count = sum(1 for ind in positive_indicators if ind in description)
        negative_count = sum(1 for ind in negative_indicators if ind in description)

        if positive_count + negative_count == 0:
            return 0.5

        return 0.3 + 0.4 * (positive_count / (positive_count + negative_count))

    def _generate_insights(self, factors: dict[str, float]) -> list[str]:
        """Generate key insights from factor analysis.

        Args:
            factors: Analysis factors and scores.

        Returns:
            List of insight strings.
        """
        insights = []

        # Find strongest factors
        sorted_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)

        for factor_name, score in sorted_factors[:3]:
            if score > 0.6:
                insights.append(f"{factor_name} is a positive influence")
            elif score < 0.4:
                insights.append(f"{factor_name} may be a barrier")

        if not insights:
            insights.append("All factors are relatively balanced")

        return insights

    def _generate_recommendations(self, factors: dict[str, float]) -> list[str]:
        """Generate recommendations based on analysis.

        Args:
            factors: Analysis factors and scores.

        Returns:
            List of recommendation strings.
        """
        recommendations = []

        # Find lowest scoring factors
        low_factors = [(name, score) for name, score in factors.items() if score < 0.4]

        for factor_name, _ in low_factors:
            if "emotional" in factor_name:
                recommendations.append("Address emotional concerns before proceeding")
            elif "trait" in factor_name:
                recommendations.append("Adapt approach to match participant preferences")
            elif "situation" in factor_name:
                recommendations.append("Consider adjusting the environment or context")

        if not recommendations:
            recommendations.append("Continue current approach")

        return recommendations

    def _capture_participant_states(self) -> list[dict[str, Any]]:
        """Capture current state of all participants.

        Returns:
            List of participant state dictionaries.
        """
        states = []
        for individual in self.individuals:
            emotional_state = self._get_emotional_state(individual)
            emotions: dict[str, float] = {}
            if emotional_state is not None and hasattr(emotional_state, "to_dict"):
                emotions = emotional_state.to_dict()
            elif isinstance(emotional_state, dict):
                emotions = emotional_state

            states.append(
                {
                    "name": self._get_individual_name(individual),
                    "emotional_state": emotions,
                }
            )
        return states

    def _generate_summary(self) -> dict[str, Any]:
        """Generate aggregate summary of all runs.

        Returns:
            Summary dictionary.
        """
        total_runs = len(self._run_results)
        achieved_count = sum(1 for r in self._run_results if r.get("outcome_achieved", False))

        likelihoods = [r.get("analysis", {}).get("likelihood", 0.5) for r in self._run_results]
        avg_likelihood = sum(likelihoods) / len(likelihoods) if likelihoods else 0.5

        return {
            "total_runs": total_runs,
            "achieved_count": achieved_count,
            "achieved_percentage": achieved_count / total_runs * 100 if total_runs else 0,
            "average_likelihood": avg_likelihood,
        }

    def _format_outcome(self, run_result: dict[str, Any]) -> str:
        """Format a single outcome result.

        Args:
            run_result: Result of a single run.

        Returns:
            Formatted string.
        """
        if self.style == SimulationStyle.JSON:
            return self._format_json(run_result)
        else:
            return self._format_narrative(run_result)

    def _format_json(self, run_result: dict[str, Any]) -> str:
        """Format as JSON.

        Args:
            run_result: Result of a single run.

        Returns:
            JSON-formatted string.
        """
        output = {
            "simulation_type": "outcome_summary",
            "target_outcome": self.target_outcome,
            "outcome_achieved": run_result.get("outcome_achieved", False),
            "analysis": run_result.get("analysis", {}),
            "participant_states": run_result.get("participant_states", []),
        }
        return json.dumps(output, indent=2)

    def _format_narrative(self, run_result: dict[str, Any]) -> str:
        """Format as narrative text.

        Args:
            run_result: Result of a single run.

        Returns:
            Narrative-formatted string.
        """
        analysis = run_result.get("analysis", {})
        achieved = run_result.get("outcome_achieved", False)
        likelihood = analysis.get("likelihood", 0.5)

        lines = [
            "=== Outcome Analysis ===",
            f"Target Outcome: {self.target_outcome}",
            "",
            f"Result: {'ACHIEVED' if achieved else 'NOT ACHIEVED'}",
            f"Likelihood: {likelihood:.1%}",
            "",
            "--- Factor Analysis ---",
        ]

        factors = analysis.get("factors", {})
        for factor_name, score in sorted(factors.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            lines.append(f"  {factor_name}: [{bar}] {score:.2f}")

        lines.append("")
        lines.append("--- Key Insights ---")
        for insight in analysis.get("key_insights", []):
            lines.append(f"  • {insight}")

        lines.append("")
        lines.append("--- Recommendations ---")
        for rec in analysis.get("recommendations", []):
            lines.append(f"  → {rec}")

        return "\n".join(lines)

    def _format_summary(self, summary: dict[str, Any]) -> str:
        """Format aggregate summary.

        Args:
            summary: Summary dictionary.

        Returns:
            Formatted summary string.
        """
        lines = [
            "=== Outcome Summary ===",
            f"Target Outcome: {self.target_outcome}",
            f"Total Simulations: {summary['total_runs']}",
            "",
            "Results:",
            f"  - Outcome Achieved: {summary['achieved_count']}/{summary['total_runs']} "
            f"({summary['achieved_percentage']:.0f}%)",
            f"  - Outcome Not Achieved: "
            f"{summary['total_runs'] - summary['achieved_count']}/{summary['total_runs']} "
            f"({100 - summary['achieved_percentage']:.0f}%)",
            "",
            f"Average Likelihood: {summary['average_likelihood']:.1%}",
        ]

        return "\n".join(lines)


__all__ = ["OutcomeSimulation"]
