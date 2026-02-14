"""Pytest configuration for integration tests.

This module provides shared fixtures and configuration for integration tests.
Integration tests require active API credentials and network access.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Callable

import pytest

if TYPE_CHECKING:
    from personaut.models.model import Model, EmbeddingModel


def pytest_configure(config: Any) -> None:
    """Configure pytest markers for integration tests."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line(
        "markers",
        "gemini: marks tests that require Gemini API",
    )
    config.addinivalue_line(
        "markers",
        "bedrock: marks tests that require AWS Bedrock",
    )


@pytest.fixture(scope="session")
def has_gemini_key() -> bool:
    """Check if Gemini API key is available."""
    return bool(os.environ.get("GOOGLE_API_KEY"))


@pytest.fixture(scope="session")
def has_bedrock_credentials() -> bool:
    """Check if AWS Bedrock credentials are available."""
    return bool(
        os.environ.get("AWS_ACCESS_KEY_ID")
        and os.environ.get("AWS_SECRET_ACCESS_KEY")
    )


@pytest.fixture(scope="session")
def has_any_api_key(has_gemini_key: bool, has_bedrock_credentials: bool) -> bool:
    """Check if any API credentials are available."""
    return has_gemini_key or has_bedrock_credentials


@pytest.fixture(scope="session")
def available_provider(has_gemini_key: bool, has_bedrock_credentials: bool) -> str | None:
    """Get an available provider name."""
    if has_gemini_key:
        return "gemini"
    elif has_bedrock_credentials:
        return "bedrock"
    return None


@pytest.fixture(scope="session")
def llm(available_provider: str | None) -> "Model | None":
    """Get an LLM model from an available provider."""
    if not available_provider:
        return None

    from personaut.models import get_llm, Provider

    if available_provider == "gemini":
        return get_llm(Provider.GEMINI)
    elif available_provider == "bedrock":
        return get_llm(Provider.BEDROCK)
    return None


@pytest.fixture(scope="session")
def embedding_model(available_provider: str | None) -> "EmbeddingModel | None":
    """Get an embedding model from an available provider."""
    if not available_provider:
        return None

    from personaut.models import get_embedding, Provider

    if available_provider == "gemini":
        return get_embedding(Provider.GEMINI)
    elif available_provider == "bedrock":
        return get_embedding(Provider.BEDROCK)
    return None


@pytest.fixture(scope="session")
def embed_func(embedding_model: "EmbeddingModel | None") -> Callable[[str], list[float]] | None:
    """Get an embedding function."""
    if not embedding_model:
        return None
    return embedding_model.embed


@pytest.fixture
def require_api(has_any_api_key: bool) -> None:
    """Skip test if no API credentials are available."""
    if not has_any_api_key:
        pytest.skip("No API credentials available")
