"""Base simulation class for Personaut PDK.

This module provides the abstract Simulation base class and factory function
for creating simulations.

Example:
    >>> from personaut.simulations import create_simulation, SimulationType
    >>> simulation = create_simulation(
    ...     situation=situation,
    ...     individuals=[user_a, user_b],
    ...     type=SimulationType.CONVERSATION,
    ... )
    >>> results = simulation.run(num=10, dir="./")
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from personaut.simulations.styles import SimulationStyle, parse_simulation_style
from personaut.simulations.types import SimulationType, parse_simulation_type


if TYPE_CHECKING:
    from personaut.situations.situation import Situation


@dataclass
class SimulationResult:
    """Result of a single simulation run.

    Attributes:
        simulation_id: Unique identifier for this run.
        simulation_type: Type of simulation that produced this result.
        content: Generated content (dialogue, responses, etc.).
        metadata: Additional metadata about the run.
        created_at: Timestamp when the simulation completed.
        output_path: Path where the result was saved (if any).

    Example:
        >>> result = SimulationResult(
        ...     simulation_id="sim_001",
        ...     simulation_type=SimulationType.CONVERSATION,
        ...     content="SARAH: Hello!\\nMIKE: Hi there!",
        ... )
    """

    simulation_id: str
    simulation_type: SimulationType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    output_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "simulation_id": self.simulation_id,
            "simulation_type": self.simulation_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "output_path": str(self.output_path) if self.output_path else None,
        }

    def to_json(self) -> str:
        """Convert result to JSON string.

        Returns:
            JSON representation of the result.
        """
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class Simulation(ABC):
    """Abstract base class for all simulations.

    Simulations orchestrate interactions between individuals based on
    their emotional states, personality traits, memories, relationships,
    and situational context.

    Attributes:
        situation: The situational context for the simulation.
        individuals: List of individuals participating.
        simulation_type: Type of simulation (conversation, survey, etc.).
        style: Output formatting style.
        output_format: File format for output (json, txt).
        relationships: Relationships between individuals.
        context: Additional situational context facts.

    Example:
        >>> class MySimulation(Simulation):
        ...     def _generate(self, **kwargs) -> str:
        ...         return "Generated content"
    """

    situation: Situation
    individuals: list[Any]
    simulation_type: SimulationType
    style: SimulationStyle | None = None
    output_format: str = "txt"
    relationships: list[Any] = field(default_factory=list)
    context: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Initialize default values after dataclass construction."""
        if self.style is None:
            default_style = self.simulation_type.default_style
            self.style = parse_simulation_style(default_style)

    def run(
        self,
        num: int = 1,
        dir: str | Path = "./",
        **options: Any,
    ) -> list[SimulationResult]:
        """Run the simulation.

        Args:
            num: Number of simulation variations to generate.
            dir: Output directory for results.
            **options: Additional simulation-specific options.

        Returns:
            List of SimulationResult objects.

        Raises:
            AgeRestrictionError: If any participating individual is under 18.

        Example:
            >>> results = simulation.run(num=10, dir="./output")
            >>> print(len(results))
            10
        """
        # Remember what Uncle Ben said: "With great power comes great
        # responsibility." Don't be a creep!
        self._validate_participant_ages()

        output_dir = Path(dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for i in range(num):
            simulation_id = f"{self.simulation_type.value}_{uuid.uuid4().hex[:8]}"

            # Generate content
            content = self._generate(run_index=i, **options)

            # Determine output path
            extension = self.style.extension if self.style else "txt"
            output_path = output_dir / f"{simulation_id}.{extension}"

            # Save to file
            self._save_output(output_path, content)

            # Create result
            result = SimulationResult(
                simulation_id=simulation_id,
                simulation_type=self.simulation_type,
                content=content,
                metadata=self._get_metadata(),
                output_path=output_path,
            )
            results.append(result)

        return results

    @abstractmethod
    def _generate(self, run_index: int = 0, **options: Any) -> str:
        """Generate simulation content.

        This method must be implemented by subclasses to produce
        the actual simulation output.

        Args:
            run_index: Index of this run (0-based).
            **options: Simulation-specific options.

        Returns:
            Generated content as a string.
        """
        ...

    def _save_output(self, path: Path, content: str) -> None:
        """Save content to file.

        Args:
            path: Output file path.
            content: Content to save.
        """
        path.write_text(content, encoding="utf-8")

    def _get_metadata(self) -> dict[str, Any]:
        """Get metadata about the simulation.

        Returns:
            Dictionary of metadata.
        """
        return {
            "situation_description": getattr(self.situation, "description", str(self.situation)),
            "participants": [self._get_individual_name(ind) for ind in self.individuals],
            "simulation_type": self.simulation_type.value,
            "style": self.style.value if self.style else None,
            "output_format": self.output_format,
        }

    def _get_individual_name(self, individual: Any) -> str:
        """Get name from an individual object.

        Args:
            individual: Individual object.

        Returns:
            Name string.
        """
        if hasattr(individual, "name"):
            return str(individual.name)
        if isinstance(individual, dict):
            return str(individual.get("name", "Unknown"))
        return "Unknown"

    def _get_emotional_state(self, individual: Any) -> Any | None:
        """Get emotional state from an individual.

        Args:
            individual: Individual object.

        Returns:
            Emotional state or None.
        """
        if hasattr(individual, "emotional_state"):
            return individual.emotional_state
        if isinstance(individual, dict):
            return individual.get("emotional_state")
        return None

    def _get_traits(self, individual: Any) -> Any | None:
        """Get traits from an individual.

        Args:
            individual: Individual object.

        Returns:
            Trait profile or None.
        """
        if hasattr(individual, "traits"):
            return individual.traits
        if isinstance(individual, dict):
            return individual.get("traits")
        return None

    def _validate_participant_ages(self) -> None:
        """Check that all participants meet the minimum age requirement.

        Raises:
            AgeRestrictionError: If any individual has age < 18.
        """
        from personaut.types.exceptions import MINIMUM_SIMULATION_AGE, AgeRestrictionError

        for individual in self.individuals:
            age = None
            name = self._get_individual_name(individual)

            if hasattr(individual, "age"):
                age = individual.age
            elif isinstance(individual, dict):
                age = individual.get("age")

            if age is not None and age < MINIMUM_SIMULATION_AGE:
                raise AgeRestrictionError(age, name=name)


def create_simulation(
    situation: Situation | Any,
    individuals: list[Any],
    type: SimulationType | str,
    style: SimulationStyle | str | None = None,
    output: str = "txt",
    context: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Simulation:
    """Factory function to create appropriate simulation type.

    Args:
        situation: Situational context for the simulation.
        individuals: List of participating individuals.
        type: Type of simulation to create.
        style: Output style (defaults to simulation type's default).
        output: Output file format (json, txt).
        context: Additional situational context.
        **kwargs: Additional arguments passed to specific simulation types.

    Returns:
        Appropriate Simulation subclass instance.

    Raises:
        ValueError: If simulation type is not supported.

    Example:
        >>> simulation = create_simulation(
        ...     situation=coffee_shop,
        ...     individuals=[sarah, mike],
        ...     type=SimulationType.CONVERSATION,
        ...     style=SimulationStyle.SCRIPT,
        ... )
    """
    # Import here to avoid circular imports
    from personaut.simulations.conversation import ConversationSimulation
    from personaut.simulations.live import LiveSimulation
    from personaut.simulations.outcome import OutcomeSimulation
    from personaut.simulations.survey import SurveySimulation

    sim_type = parse_simulation_type(type)
    sim_style = parse_simulation_style(style) if style else None

    simulation_classes = {
        SimulationType.CONVERSATION: ConversationSimulation,
        SimulationType.SURVEY: SurveySimulation,
        SimulationType.OUTCOME_SUMMARY: OutcomeSimulation,
        SimulationType.LIVE_CONVERSATION: LiveSimulation,
    }

    simulation_cls = simulation_classes.get(sim_type)
    if simulation_cls is None:
        msg = f"Unsupported simulation type: {sim_type}"
        raise ValueError(msg)

    instance = simulation_cls(
        situation=situation,
        individuals=individuals,
        simulation_type=sim_type,
        style=sim_style,
        output_format=output,
        context=context,
        **kwargs,
    )
    # Cast needed because mypy cannot infer subclass type from dict lookup
    from typing import cast

    return cast("Simulation", instance)


__all__ = [
    "Simulation",
    "SimulationResult",
    "create_simulation",
]
