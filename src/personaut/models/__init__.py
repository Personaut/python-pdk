"""LLM model providers for Personaut PDK.

This module provides interfaces for text generation and embedding models
from various providers including Gemini, Bedrock, OpenAI, Anthropic, and Ollama.

The PDK uses a **local-first embedding strategy** where embeddings are
always generated locally using sentence-transformers. This ensures
consistent vector representations across all LLM providers.

Quick Start:
    >>> from personaut.models import get_llm, get_embedding
    >>>
    >>> # Get LLM (auto-detects from environment)
    >>> llm = get_llm()
    >>> result = llm.generate("Explain quantum computing")
    >>> print(result.text)
    >>>
    >>> # Get embedding model (always local)
    >>> embed = get_embedding()
    >>> vector = embed.embed("Hello, world!")

Provider Examples:
    >>> from personaut.models import GeminiModel, OpenAIModel
    >>>
    >>> # Gemini (requires GOOGLE_API_KEY)
    >>> gemini = GeminiModel()
    >>> gemini.generate("Write a haiku")
    >>>
    >>> # OpenAI (requires OPENAI_API_KEY)
    >>> openai = OpenAIModel()
    >>> openai.generate("Explain gravity")
    >>>
    >>> # Bedrock (uses AWS credentials)
    >>> from personaut.models import BedrockModel
    >>> bedrock = BedrockModel(model="claude-3-5-sonnet")
    >>>
    >>> # Ollama (local, requires Ollama running)
    >>> from personaut.models import OllamaModel
    >>> ollama = OllamaModel(model="llama3.2")

Configuration:
    Environment variables:
    - PERSONAUT_LLM_PROVIDER: Default LLM provider (gemini, openai, anthropic, bedrock, ollama)
    - PERSONAUT_LLM_MODEL: Default model name
    - PERSONAUT_EMBEDDING_MODEL: Embedding model (default: all-MiniLM-L6-v2)

    Provider-specific:
    - GOOGLE_API_KEY: For Gemini
    - OPENAI_API_KEY: For OpenAI
    - ANTHROPIC_API_KEY: For Anthropic (Claude)
    - AWS credentials: For Bedrock (via boto3)
"""

# Base interfaces
# Embedding interfaces
from personaut.models.embeddings import (
    DEFAULT_MODEL_LARGE,
    DEFAULT_MODEL_SMALL,
    EMBEDDING_MODELS,
    EmbeddingConfig,
    EmbeddingError,
    EmbeddingModel,
    ModelLoadError,
    ModelNotLoadedError,
    TextTooLongError,
)

# Local embedding
from personaut.models.local_embedding import (
    LocalEmbedding,
    create_local_embedding,
)
from personaut.models.model import (
    AsyncModel,
    AuthenticationError,
    GenerationResult,
    InvalidRequestError,
    Model,
    ModelConfig,
    ModelError,
    RateLimitError,
)


# LLM Providers (imported lazily to avoid requiring all dependencies)
# Use try/except to allow imports without all providers installed


def _lazy_import_gemini() -> tuple[type, object, str, list[str]]:
    from personaut.models.gemini import (
        AVAILABLE_GEMINI_MODELS,
        DEFAULT_GEMINI_MODEL,
        GeminiModel,
        create_gemini_model,
    )

    return GeminiModel, create_gemini_model, DEFAULT_GEMINI_MODEL, AVAILABLE_GEMINI_MODELS


def _lazy_import_openai() -> tuple[type, object, str, list[str]]:
    from personaut.models.openai import (
        AVAILABLE_OPENAI_MODELS,
        DEFAULT_OPENAI_MODEL,
        OpenAIModel,
        create_openai_model,
    )

    return OpenAIModel, create_openai_model, DEFAULT_OPENAI_MODEL, AVAILABLE_OPENAI_MODELS


def _lazy_import_bedrock() -> tuple[type, object, dict[str, str], str]:
    from personaut.models.bedrock import (
        BEDROCK_MODELS,
        DEFAULT_BEDROCK_MODEL,
        BedrockModel,
        create_bedrock_model,
    )

    return BedrockModel, create_bedrock_model, BEDROCK_MODELS, DEFAULT_BEDROCK_MODEL


def _lazy_import_ollama() -> tuple[type, object, str, str]:
    from personaut.models.ollama import (
        DEFAULT_OLLAMA_HOST,
        DEFAULT_OLLAMA_MODEL,
        OllamaModel,
        create_ollama_model,
    )

    return OllamaModel, create_ollama_model, DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_HOST


def _lazy_import_anthropic() -> tuple[type, object, str, list[str]]:
    from personaut.models.anthropic import (
        AVAILABLE_ANTHROPIC_MODELS,
        DEFAULT_ANTHROPIC_MODEL,
        AnthropicModel,
        create_anthropic_model,
    )

    return AnthropicModel, create_anthropic_model, DEFAULT_ANTHROPIC_MODEL, AVAILABLE_ANTHROPIC_MODELS


# Registry
from personaut.models.registry import (
    ENV_EMBEDDING_MODEL,
    ENV_LLM_MODEL,
    ENV_LLM_PROVIDER,
    ModelRegistry,
    Provider,
    get_embedding,
    get_llm,
    get_registry,
)


# Lazy loading for provider classes
def __getattr__(name: str) -> object:
    """Lazy load provider classes."""
    if name in ("GeminiModel", "create_gemini_model", "DEFAULT_GEMINI_MODEL", "AVAILABLE_GEMINI_MODELS"):
        gemini_exports = _lazy_import_gemini()
        gemini_mapping: dict[str, object] = {
            "GeminiModel": gemini_exports[0],
            "create_gemini_model": gemini_exports[1],
            "DEFAULT_GEMINI_MODEL": gemini_exports[2],
            "AVAILABLE_GEMINI_MODELS": gemini_exports[3],
        }
        return gemini_mapping[name]

    elif name in ("OpenAIModel", "create_openai_model", "DEFAULT_OPENAI_MODEL", "AVAILABLE_OPENAI_MODELS"):
        openai_exports = _lazy_import_openai()
        openai_mapping: dict[str, object] = {
            "OpenAIModel": openai_exports[0],
            "create_openai_model": openai_exports[1],
            "DEFAULT_OPENAI_MODEL": openai_exports[2],
            "AVAILABLE_OPENAI_MODELS": openai_exports[3],
        }
        return openai_mapping[name]

    elif name in ("BedrockModel", "create_bedrock_model", "BEDROCK_MODELS", "DEFAULT_BEDROCK_MODEL"):
        bedrock_exports = _lazy_import_bedrock()
        bedrock_mapping: dict[str, object] = {
            "BedrockModel": bedrock_exports[0],
            "create_bedrock_model": bedrock_exports[1],
            "BEDROCK_MODELS": bedrock_exports[2],
            "DEFAULT_BEDROCK_MODEL": bedrock_exports[3],
        }
        return bedrock_mapping[name]

    elif name in ("AnthropicModel", "create_anthropic_model", "DEFAULT_ANTHROPIC_MODEL", "AVAILABLE_ANTHROPIC_MODELS"):
        anthropic_exports = _lazy_import_anthropic()
        anthropic_mapping: dict[str, object] = {
            "AnthropicModel": anthropic_exports[0],
            "create_anthropic_model": anthropic_exports[1],
            "DEFAULT_ANTHROPIC_MODEL": anthropic_exports[2],
            "AVAILABLE_ANTHROPIC_MODELS": anthropic_exports[3],
        }
        return anthropic_mapping[name]

    elif name in ("OllamaModel", "create_ollama_model", "DEFAULT_OLLAMA_MODEL", "DEFAULT_OLLAMA_HOST"):
        ollama_exports = _lazy_import_ollama()
        ollama_mapping: dict[str, object] = {
            "OllamaModel": ollama_exports[0],
            "create_ollama_model": ollama_exports[1],
            "DEFAULT_OLLAMA_MODEL": ollama_exports[2],
            "DEFAULT_OLLAMA_HOST": ollama_exports[3],
        }
        return ollama_mapping[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Base interfaces
    "Model",
    "AsyncModel",
    "ModelConfig",
    "GenerationResult",
    # Model errors
    "ModelError",
    "RateLimitError",
    "AuthenticationError",
    "InvalidRequestError",
    # Embedding interfaces
    "EmbeddingModel",
    "EmbeddingConfig",
    "EmbeddingError",
    "ModelLoadError",
    "ModelNotLoadedError",
    "TextTooLongError",
    "EMBEDDING_MODELS",
    "DEFAULT_MODEL_LARGE",
    "DEFAULT_MODEL_SMALL",
    # Local embedding
    "LocalEmbedding",
    "create_local_embedding",
    # Registry
    "ModelRegistry",
    "Provider",
    "get_registry",
    "get_llm",
    "get_embedding",
    "ENV_LLM_PROVIDER",
    "ENV_LLM_MODEL",
    "ENV_EMBEDDING_MODEL",
    # Gemini (lazy)
    "GeminiModel",
    "create_gemini_model",
    "DEFAULT_GEMINI_MODEL",
    "AVAILABLE_GEMINI_MODELS",
    # OpenAI (lazy)
    "OpenAIModel",
    "create_openai_model",
    "DEFAULT_OPENAI_MODEL",
    "AVAILABLE_OPENAI_MODELS",
    # Bedrock (lazy)
    "BedrockModel",
    "create_bedrock_model",
    "BEDROCK_MODELS",
    "DEFAULT_BEDROCK_MODEL",
    # Anthropic (lazy)
    "AnthropicModel",
    "create_anthropic_model",
    "DEFAULT_ANTHROPIC_MODEL",
    "AVAILABLE_ANTHROPIC_MODELS",
    # Ollama (lazy)
    "OllamaModel",
    "create_ollama_model",
    "DEFAULT_OLLAMA_MODEL",
    "DEFAULT_OLLAMA_HOST",
]
