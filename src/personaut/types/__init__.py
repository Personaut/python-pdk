"""Type definitions for Personaut PDK.

This module provides common types, enums, exceptions, and protocols used
throughout the Personaut PDK.

Example:
    >>> from personaut.types import Modality, IndividualType
    >>> from personaut.types.exceptions import ValidationError, EmotionValueError
    >>> from personaut.types.common import EmotionDict, TraitDict
"""

from personaut.types.common import (
    EmbeddingModelProtocol,
    EmbeddingVector,
    EmotionalStateProtocol,
    EmotionDict,
    IndividualProtocol,
    IndividualT,
    JsonDict,
    MemoryProtocol,
    MemoryT,
    ModelProtocol,
    OnCompleteCallback,
    OnEmotionChangeCallback,
    OnTurnCallback,
    T,
    T_co,
    TraitDict,
    TrustDict,
    VectorStoreProtocol,
)
from personaut.types.exceptions import (
    ConfigurationError,
    EmotionNotFoundError,
    EmotionValueError,
    MemoryError,
    ModelError,
    PersonautError,
    SimulationError,
    TraitNotFoundError,
    TraitValueError,
    TrustThresholdError,
    ValidationError,
)
from personaut.types.individual import (
    HUMAN,
    NONTRACKED,
    SIMULATED,
    IndividualType,
    parse_individual_type,
)
from personaut.types.modality import (
    EMAIL,
    IN_PERSON,
    PHONE_CALL,
    SURVEY,
    TEXT_MESSAGE,
    VIDEO_CALL,
    Modality,
    parse_modality,
)


__all__ = [
    # Modality
    "EMAIL",
    # Individual types
    "HUMAN",
    "IN_PERSON",
    "NONTRACKED",
    "PHONE_CALL",
    "SIMULATED",
    "SURVEY",
    "TEXT_MESSAGE",
    "VIDEO_CALL",
    # Exceptions
    "ConfigurationError",
    # Protocols
    "EmbeddingModelProtocol",
    # Common type aliases
    "EmbeddingVector",
    "EmotionDict",
    "EmotionNotFoundError",
    "EmotionValueError",
    "EmotionalStateProtocol",
    "IndividualProtocol",
    # TypeVars
    "IndividualT",
    "IndividualType",
    "JsonDict",
    "MemoryError",
    "MemoryProtocol",
    "MemoryT",
    "Modality",
    "ModelError",
    "ModelProtocol",
    # Callbacks
    "OnCompleteCallback",
    "OnEmotionChangeCallback",
    "OnTurnCallback",
    "PersonautError",
    "SimulationError",
    "T",
    "T_co",
    "TraitDict",
    "TraitNotFoundError",
    "TraitValueError",
    "TrustDict",
    "TrustThresholdError",
    "ValidationError",
    "VectorStoreProtocol",
    "parse_individual_type",
    "parse_modality",
]
