"""Masks module for Personaut PDK.

Masks are contextual personas that modify emotional expression based on
situational context. They allow individuals to adapt their behavior to
different social contexts while maintaining their underlying emotional state.

Basic Usage:
    >>> from personaut.masks import Mask, create_mask
    >>>
    >>> # Create a custom mask
    >>> my_mask = create_mask(
    ...     name="interview",
    ...     emotional_modifications={"anxious": -0.3, "confident": 0.4},
    ...     trigger_situations=["interview", "formal"],
    ... )
    >>>
    >>> # Apply to emotional state
    >>> modified_state = my_mask.apply(emotional_state)

Using Predefined Masks:
    >>> from personaut.masks import PROFESSIONAL_MASK, STOIC_MASK
    >>>
    >>> # Check if mask should activate
    >>> if PROFESSIONAL_MASK.should_trigger("office meeting"):
    ...     state = PROFESSIONAL_MASK.apply(state)

Available Masks:
    - PROFESSIONAL_MASK: Workplace persona, suppresses strong emotions
    - CASUAL_MASK: Relaxed social persona, allows natural expression
    - STOIC_MASK: Crisis persona, promotes calm and measured responses
    - ENTHUSIASTIC_MASK: Motivational persona, amplifies positive emotions
    - NURTURING_MASK: Caretaking persona, promotes warmth and patience
    - GUARDED_MASK: Protective persona, reduces trust in unfamiliar situations
"""

from personaut.masks.defaults import (
    CASUAL_MASK,
    DEFAULT_MASKS,
    ENTHUSIASTIC_MASK,
    GUARDED_MASK,
    NURTURING_MASK,
    PROFESSIONAL_MASK,
    STOIC_MASK,
    get_mask_by_name,
)
from personaut.masks.mask import Mask, create_mask


__all__ = [
    # Core classes
    "Mask",
    "create_mask",
    # Predefined masks
    "PROFESSIONAL_MASK",
    "CASUAL_MASK",
    "STOIC_MASK",
    "ENTHUSIASTIC_MASK",
    "NURTURING_MASK",
    "GUARDED_MASK",
    # Utilities
    "DEFAULT_MASKS",
    "get_mask_by_name",
]
