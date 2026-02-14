"""State calculator for Personaut PDK.

This module provides the StateCalculator class for computing emotional
states from a history of past states using configurable calculation modes.

Example:
    >>> from personaut.states.calculator import StateCalculator
    >>> from personaut.states.mode import StateMode
    >>> from personaut.emotions import EmotionalState
    >>>
    >>> calc = StateCalculator(mode=StateMode.AVERAGE, history_size=5)
    >>> calc.add_state(EmotionalState())
    >>> calculated = calc.get_calculated_state()
"""

from __future__ import annotations

from collections.abc import Callable

from personaut.emotions.state import EmotionalState
from personaut.states.mode import StateMode


# Type alias for custom calculation functions
CustomCalculator = Callable[[list[EmotionalState]], EmotionalState]


class StateCalculator:
    """Calculator for computing emotional state from history.

    StateCalculator maintains a history of emotional states and provides
    methods to compute a single representative state using various
    calculation strategies (modes).

    Attributes:
        mode: The calculation mode to use.
        history_size: Maximum number of states to keep in history.
        decay_factor: For RECENT mode, the exponential decay factor.

    Example:
        >>> calc = StateCalculator(mode=StateMode.AVERAGE)
        >>> state1 = EmotionalState()
        >>> state1.change_emotion("anxious", 0.8)
        >>> calc.add_state(state1)
        >>> state2 = EmotionalState()
        >>> state2.change_emotion("anxious", 0.4)
        >>> calc.add_state(state2)
        >>> result = calc.get_calculated_state()
        >>> result.get_emotion("anxious")  # Average of 0.8 and 0.4
        0.6
    """

    __slots__ = ("_custom_function", "_decay_factor", "_history", "_history_size", "_mode")

    def __init__(
        self,
        mode: StateMode = StateMode.AVERAGE,
        history_size: int = 10,
        decay_factor: float = 0.8,
        custom_function: CustomCalculator | None = None,
    ) -> None:
        """Initialize a StateCalculator.

        Args:
            mode: The calculation mode to use.
            history_size: Maximum number of states to keep in history.
            decay_factor: For RECENT mode, the exponential decay factor (0-1).
                Higher values weight recent states more heavily.
            custom_function: Function for CUSTOM mode. Must accept a list
                of EmotionalState and return an EmotionalState.

        Raises:
            ValueError: If mode is CUSTOM but no custom_function provided.
            ValueError: If history_size is less than 1.
            ValueError: If decay_factor is not between 0 and 1.

        Example:
            >>> calc = StateCalculator(mode=StateMode.MAXIMUM, history_size=5)
        """
        if mode == StateMode.CUSTOM and custom_function is None:
            msg = "custom_function is required when mode is CUSTOM"
            raise ValueError(msg)

        if history_size < 1:
            msg = f"history_size must be at least 1, got {history_size}"
            raise ValueError(msg)

        if not 0.0 <= decay_factor <= 1.0:
            msg = f"decay_factor must be between 0 and 1, got {decay_factor}"
            raise ValueError(msg)

        self._mode = mode
        self._history_size = history_size
        self._decay_factor = decay_factor
        self._custom_function = custom_function
        self._history: list[EmotionalState] = []

    @property
    def mode(self) -> StateMode:
        """Get the current calculation mode."""
        return self._mode

    @property
    def history_size(self) -> int:
        """Get the maximum history size."""
        return self._history_size

    @property
    def decay_factor(self) -> float:
        """Get the decay factor for RECENT mode."""
        return self._decay_factor

    def add_state(self, state: EmotionalState) -> None:
        """Add an emotional state to the history.

        If the history exceeds the maximum size, the oldest state
        is removed.

        Args:
            state: The emotional state to add.

        Example:
            >>> calc = StateCalculator()
            >>> state = EmotionalState()
            >>> state.change_emotion("anxious", 0.7)
            >>> calc.add_state(state)
        """
        self._history.append(state.copy())

        # Trim to history_size
        while len(self._history) > self._history_size:
            self._history.pop(0)

    def clear_history(self) -> None:
        """Clear all states from the history.

        Example:
            >>> calc = StateCalculator()
            >>> calc.add_state(EmotionalState())
            >>> calc.clear_history()
            >>> len(calc.get_history())
            0
        """
        self._history.clear()

    def get_history(self) -> list[EmotionalState]:
        """Get a copy of the state history.

        Returns:
            List of emotional states in chronological order.

        Example:
            >>> calc = StateCalculator()
            >>> calc.add_state(EmotionalState())
            >>> history = calc.get_history()
            >>> len(history)
            1
        """
        return [state.copy() for state in self._history]

    def calculate(self, history: list[EmotionalState]) -> EmotionalState:
        """Calculate a state from the given history.

        Args:
            history: List of emotional states to process.

        Returns:
            A new EmotionalState representing the calculated result.

        Raises:
            ValueError: If history is empty.

        Example:
            >>> calc = StateCalculator(mode=StateMode.AVERAGE)
            >>> states = [EmotionalState(), EmotionalState()]
            >>> result = calc.calculate(states)
        """
        if not history:
            msg = "Cannot calculate from empty history"
            raise ValueError(msg)

        if self._mode == StateMode.AVERAGE:
            return self._calculate_average(history)
        if self._mode == StateMode.MAXIMUM:
            return self._calculate_maximum(history)
        if self._mode == StateMode.MINIMUM:
            return self._calculate_minimum(history)
        if self._mode == StateMode.RECENT:
            return self._calculate_recent(history)
        if self._mode == StateMode.CUSTOM and self._custom_function:
            return self._custom_function(history)

        # Fallback (shouldn't happen)
        return self._calculate_average(history)

    def get_calculated_state(self) -> EmotionalState:
        """Calculate state from the internal history.

        Returns:
            A new EmotionalState representing the calculated result.
            If history is empty, returns a neutral state.

        Example:
            >>> calc = StateCalculator()
            >>> calc.add_state(EmotionalState())
            >>> result = calc.get_calculated_state()
        """
        if not self._history:
            return EmotionalState()

        return self.calculate(self._history)

    def _calculate_average(self, history: list[EmotionalState]) -> EmotionalState:
        """Calculate average intensity for each emotion.

        Args:
            history: List of emotional states.

        Returns:
            EmotionalState with averaged values.
        """
        # Get emotion names from first state
        emotions = list(history[0])

        result = EmotionalState(emotions=emotions)

        for emotion in emotions:
            total = sum(state.get_emotion(emotion) for state in history if emotion in state)
            count = sum(1 for state in history if emotion in state)
            if count > 0:
                result.change_emotion(emotion, total / count)

        return result

    def _calculate_maximum(self, history: list[EmotionalState]) -> EmotionalState:
        """Calculate maximum intensity for each emotion.

        Args:
            history: List of emotional states.

        Returns:
            EmotionalState with maximum values.
        """
        emotions = list(history[0])
        result = EmotionalState(emotions=emotions)

        for emotion in emotions:
            max_val = max(
                (state.get_emotion(emotion) for state in history if emotion in state),
                default=0.0,
            )
            result.change_emotion(emotion, max_val)

        return result

    def _calculate_minimum(self, history: list[EmotionalState]) -> EmotionalState:
        """Calculate minimum intensity for each emotion.

        Args:
            history: List of emotional states.

        Returns:
            EmotionalState with minimum values.
        """
        emotions = list(history[0])
        result = EmotionalState(emotions=emotions)

        for emotion in emotions:
            values = [state.get_emotion(emotion) for state in history if emotion in state]
            if values:
                result.change_emotion(emotion, min(values))

        return result

    def _calculate_recent(self, history: list[EmotionalState]) -> EmotionalState:
        """Calculate weighted average with exponential decay.

        More recent states have higher weights using the decay factor.

        Args:
            history: List of emotional states (oldest first).

        Returns:
            EmotionalState with weighted values.
        """
        emotions = list(history[0])
        result = EmotionalState(emotions=emotions)

        n = len(history)
        weights = [self._decay_factor ** (n - 1 - i) for i in range(n)]
        total_weight = sum(weights)

        for emotion in emotions:
            weighted_sum = sum(
                state.get_emotion(emotion) * weights[i] for i, state in enumerate(history) if emotion in state
            )
            if total_weight > 0:
                result.change_emotion(emotion, weighted_sum / total_weight)

        return result

    def __len__(self) -> int:
        """Return the current history size."""
        return len(self._history)

    def __repr__(self) -> str:
        """Return a string representation."""
        return f"StateCalculator(mode={self._mode.value}, history={len(self._history)}/{self._history_size})"


__all__ = [
    "CustomCalculator",
    "StateCalculator",
]
