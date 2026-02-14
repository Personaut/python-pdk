"""Portrait generation from physical feature descriptions.

Uses Google's Gemini image generation model to create character
portraits based on PhysicalFeatures data.

Example:
    >>> from personaut.individuals.physical import PhysicalFeatures
    >>> from personaut.images.portrait import generate_portrait
    >>> features = PhysicalFeatures(
    ...     hair="short dark wavy hair",
    ...     eyes="dark brown",
    ...     build="athletic",
    ... )
    >>> image_bytes = generate_portrait(features, name="Marcus")
    >>> with open("marcus.png", "wb") as f:
    ...     f.write(image_bytes)
"""

from __future__ import annotations

import logging
import os

from personaut.individuals.physical import PhysicalFeatures


logger = logging.getLogger(__name__)

# Default model for image generation
DEFAULT_IMAGE_MODEL = "gemini-2.5-flash-image"

# Portrait prompt template — designed for consistent, high-quality character portraits
_PORTRAIT_PROMPT_TEMPLATE = """Create a realistic, high-quality character portrait photograph.

Subject description:
{description}

Style requirements:
- Professional portrait photography style, head and shoulders framing
- Soft, natural lighting (like a professional headshot)
- Neutral or softly blurred background
- The person should look natural and approachable, not posed unnaturally
- Photorealistic rendering — this should look like an actual photograph
- No text, watermarks, or overlays
- The subject should be facing the camera with a natural, neutral expression
"""


def build_portrait_prompt(
    features: PhysicalFeatures,
    name: str = "",
    style: str = "photorealistic portrait",
) -> str:
    """Build an image generation prompt from physical features.

    Translates the structured PhysicalFeatures data into a natural-language
    description suitable for image generation models.

    Args:
        features: The individual's physical features.
        name: Optional name (used for context, not included in prompt to
              avoid text rendering attempts).
        style: Art/photo style descriptor.

    Returns:
        A text prompt for image generation.

    Example:
        >>> features = PhysicalFeatures(hair="red", eyes="green", build="slim")
        >>> prompt = build_portrait_prompt(features)
        >>> "red" in prompt
        True
    """
    parts: list[str] = []

    if features.age_appearance:
        parts.append(f"A person who appears to be {features.age_appearance}")
    else:
        parts.append("A person")

    if features.build:
        parts.append(f"with a {features.build} build")

    if features.height:
        parts.append(f"({features.height} tall)")

    if features.skin_tone:
        parts.append(f"with {features.skin_tone} skin")

    if features.hair:
        parts.append(f"and {features.hair}")

    if features.eyes:
        parts.append(f"with {features.eyes} eyes")

    if features.facial_features:
        parts.append(f"— {features.facial_features}")

    if features.distinguishing_features:
        visible = [
            f
            for f in features.distinguishing_features
            if any(
                kw in f.lower()
                for kw in [
                    "scar",
                    "freckle",
                    "mole",
                    "piercing",
                    "tattoo",
                    "birthmark",
                    "dimple",
                    "wrinkle",
                    "beard",
                    "mustache",
                ]
            )
        ]
        if visible:
            parts.append(f"Notable features: {', '.join(visible)}")

    if features.accessories:
        wearable = [
            a
            for a in features.accessories
            if any(
                kw in a.lower()
                for kw in [
                    "glasses",
                    "earring",
                    "necklace",
                    "hat",
                    "cap",
                    "headband",
                    "scarf",
                    "bandana",
                    "ring",
                ]
            )
        ]
        if wearable:
            parts.append(f"Wearing: {', '.join(wearable)}")

    if features.clothing_style:
        parts.append(f"Dressed in {features.clothing_style} clothing")

    description = " ".join(parts) + "."

    return _PORTRAIT_PROMPT_TEMPLATE.format(description=description)


def generate_portrait(
    features: PhysicalFeatures,
    name: str = "",
    *,
    api_key: str | None = None,
    model: str = DEFAULT_IMAGE_MODEL,
    aspect_ratio: str = "1:1",
) -> bytes | None:
    """Generate a portrait image from physical features.

    Uses the Gemini image generation model to create a character portrait
    based on the individual's physical description.

    Args:
        features: Physical features to base the portrait on.
        name: Individual's name (for logging; not sent to the model).
        api_key: Google API key. Falls back to GOOGLE_API_KEY env var.
        model: Image generation model name.
        aspect_ratio: Output aspect ratio (e.g., "1:1", "3:4").

    Returns:
        PNG image bytes if successful, None if generation fails.

    Raises:
        ImportError: If google-genai is not installed.

    Example:
        >>> features = PhysicalFeatures(hair="long blonde", eyes="blue")
        >>> img = generate_portrait(features, name="Test")
        >>> # img is bytes or None
    """
    if features.is_empty():
        logger.warning("Cannot generate portrait — no physical features set")
        return None

    # Resolve API key
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        logger.warning(
            "No GOOGLE_API_KEY set — cannot generate portrait for %s",
            name or "individual",
        )
        return None

    # Import google-genai
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise ImportError(
            "google-genai is required for image generation. Install with: pip install google-genai"
        ) from e

    # Build prompt
    prompt = build_portrait_prompt(features, name=name)
    logger.info(
        "Generating portrait for %s (%d-char prompt, model=%s)",
        name or "individual",
        len(prompt),
        model,
    )

    try:
        client = genai.Client(api_key=key)

        response = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["Image"],
            ),
        )

        # Extract image from response parts
        if response.candidates and response.candidates[0].content:
            parts = response.candidates[0].content.parts
            if parts is not None:
                for part in parts:
                    if part.inline_data is not None:
                        image_bytes: bytes | None = part.inline_data.data
                        if image_bytes is not None:
                            logger.info(
                                "Portrait generated for %s (%d bytes)",
                                name or "individual",
                                len(image_bytes),
                            )
                            return image_bytes

        logger.warning(
            "Image generation returned no image data for %s",
            name or "individual",
        )
        return None

    except Exception as e:
        logger.error(
            "Portrait generation failed for %s: %s",
            name or "individual",
            e,
        )
        return None


def _get_data_dir() -> "Path":
    """Return the data directory derived from PERSONAUT_STORAGE_PATH.

    Falls back to ``./data`` when the env var is unset.
    """
    from pathlib import Path

    storage_path = os.environ.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db")
    return Path(storage_path).resolve().parent


def save_portrait(
    image_bytes: bytes,
    individual_id: str,
    output_dir: str | None = None,
) -> str:
    """Save portrait image bytes to disk.

    Args:
        image_bytes: Raw PNG image bytes.
        individual_id: The individual's ID (used as filename).
        output_dir: Directory to save into. Defaults to the
            ``portraits/`` subdirectory inside the data directory
            specified by ``PERSONAUT_STORAGE_PATH``.

    Returns:
        The relative URL path to the saved image (e.g., /data/portraits/ind_xxx.png).
    """
    from pathlib import Path

    if output_dir is None:
        portraits_dir = _get_data_dir() / "portraits"
    else:
        portraits_dir = Path(output_dir)

    portraits_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{individual_id}.png"
    filepath = portraits_dir / filename

    with open(filepath, "wb") as f:
        f.write(image_bytes)

    logger.info("Saved portrait to %s", filepath)
    return f"/data/portraits/{filename}"
