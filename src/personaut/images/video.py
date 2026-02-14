"""POV conversation video generation using Google's Veo model.

Generates a cinematic first-person-perspective video representing a
conversation between the user and an individual, using:
- Gemini to craft a cinematic video prompt from chat messages
- The individual's portrait as a starting frame (image-to-video)
- Veo 3.1 for the actual video generation

Example:
    >>> from personaut.images.video import generate_conversation_video
    >>> video_path = generate_conversation_video(
    ...     messages=[
    ...         {"role": "user", "content": "Hey, how's your day going?"},
    ...         {"role": "assistant", "content": "Pretty great! Just finished painting."},
    ...     ],
    ...     individual_name="Elena",
    ...     physical_description="A woman in her late 20s with long black curly hair...",
    ...     portrait_path="/path/to/portrait.png",
    ...     output_path="/path/to/output.mp4",
    ... )
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

# ── Model defaults ──────────────────────────────────────────────────────
DEFAULT_VEO_MODEL = "veo-3.1-fast-generate-preview"
DEFAULT_PROMPT_MODEL = "gemini-2.5-flash"
MAX_POLL_SECONDS = 300  # 5 minutes max wait
POLL_INTERVAL = 10  # seconds between polls


# ── Prompt construction ─────────────────────────────────────────────────

_SCENE_PROMPT_SYSTEM = """\
You are a cinematic director writing a video scene description for an AI video generator
that produces video WITH AUDIO including speech.

Given a chat conversation between a user and a character, write a SHORT (3-5 sentence)
first-person POV video prompt that captures the emotional essence of the conversation.
The camera should feel like YOU are there, sitting across from the character.

CRITICAL — TWO VOICES IN THE SCENE:
- The CHARACTER is ON SCREEN: We see their face and body language as they speak.
  Write their actual spoken dialogue into the scene description.
- The USER is OFF CAMERA: A separate voice is heard asking questions or responding
  from behind the camera (the viewer's perspective). Write the user's spoken lines
  as coming from an off-screen voice.
- The scene must feel like a REAL TWO-WAY conversation with both people talking.

Rules:
- Write from second-person POV ("You are sitting across from...")
- Describe what the camera SEES: the character's face, body language, environment
- The character speaks their lines ON CAMERA — include their actual dialogue
- An off-screen voice (the user, from behind the camera) speaks the user's lines
- Include ambient sounds and emotional tone
- Reference specific moments from the conversation naturally
- Keep it under 120 words — Veo works best with concise prompts
- Include the character's physical appearance naturally
- This is a SINGLE continuous shot, not a montage
- Do NOT include any text overlays, captions, or subtitles
"""

_SCENE_PROMPT_TEMPLATE = """\
Character: {name}
Physical appearance: {appearance}

Conversation (most recent {msg_count} messages):
{conversation}

Write a cinematic POV video prompt for this scene. The character ({name}) speaks
on camera while the user's voice is heard off-screen asking questions and responding.
Focus on the most emotionally compelling exchange. Both voices must be present.
"""


def build_scene_prompt(
    messages: list[dict[str, str]],
    individual_name: str,
    physical_description: str = "",
    *,
    api_key: str | None = None,
    prompt_model: str = DEFAULT_PROMPT_MODEL,
) -> str:
    """Use Gemini to craft a cinematic prompt from conversation messages.

    Args:
        messages: List of message dicts with "role" and "content" keys.
        individual_name: Name of the character.
        physical_description: Text description of their appearance.
        api_key: Google API key. Falls back to GOOGLE_API_KEY env var.
        prompt_model: LLM model for prompt generation.

    Returns:
        A cinematic video prompt string.
    """
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError("GOOGLE_API_KEY required for scene prompt generation")

    from google import genai
    from google.genai import types

    # Format conversation (last 10 messages max)
    recent = messages[-10:] if len(messages) > 10 else messages
    conv_lines = []
    for msg in recent:
        role = msg.get("role", "user")
        speaker = "You" if role == "user" else individual_name
        content = msg.get("content", "")
        # Truncate very long messages
        if len(content) > 200:
            content = content[:200] + "..."
        conv_lines.append(f"{speaker}: {content}")

    user_prompt = _SCENE_PROMPT_TEMPLATE.format(
        name=individual_name,
        appearance=physical_description or "not specified",
        msg_count=len(recent),
        conversation="\n".join(conv_lines),
    )

    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=prompt_model,
        contents=[user_prompt],
        config=types.GenerateContentConfig(
            system_instruction=_SCENE_PROMPT_SYSTEM,
            temperature=0.9,
            max_output_tokens=200,
        ),
    )

    if response.text is None:
        raise ValueError("Gemini returned empty response for scene prompt")
    prompt = response.text.strip()
    logger.info("Generated scene prompt (%d chars): %s", len(prompt), prompt[:100])
    return prompt


def generate_conversation_video(
    messages: list[dict[str, str]],
    individual_name: str,
    physical_description: str = "",
    portrait_path: str | None = None,
    output_path: str | None = None,
    session_id: str = "",
    *,
    api_key: str | None = None,
    veo_model: str = DEFAULT_VEO_MODEL,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 8,
    person_generation: str = "allow_adult",
) -> str | None:
    """Generate a POV video of a conversation using Veo.

    Pipeline:
    1. Uses Gemini to write a cinematic prompt from chat messages
    2. Optionally uses the individual's portrait as the starting frame
    3. Calls Veo 3.1 to generate the video
    4. Polls until complete and saves the MP4

    Args:
        messages: Chat messages (list of {"role": ..., "content": ...}).
        individual_name: The character's name.
        physical_description: Text description of appearance.
        portrait_path: Optional path to portrait PNG for image-to-video.
        output_path: Where to save the MP4. Auto-generated if None.
        session_id: Chat session ID (for filename).
        api_key: Google API key.
        veo_model: Veo model name.
        aspect_ratio: Video aspect ratio ("16:9" or "9:16").
        duration_seconds: Video duration (4, 6, or 8 seconds).
        person_generation: Person generation policy.

    Returns:
        Path to the saved MP4 file, or None on failure.
    """
    if not messages:
        logger.warning("No messages to generate video from")
        return None

    # Require a real conversation — messages from both participants
    has_user = any(m.get("role") == "user" for m in messages)
    has_assistant = any(m.get("role") == "assistant" for m in messages)
    if not (has_user and has_assistant):
        logger.warning(
            "Video requires a real conversation with messages from both user and %s (has_user=%s, has_assistant=%s)",
            individual_name,
            has_user,
            has_assistant,
        )
        return None

    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        logger.warning("No GOOGLE_API_KEY — cannot generate video")
        return None

    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise ImportError("google-genai required for video generation. Install with: pip install google-genai") from e

    # Step 1: Generate cinematic prompt
    logger.info(
        "Generating POV video for %s (session=%s, %d messages)",
        individual_name,
        session_id,
        len(messages),
    )
    scene_prompt = build_scene_prompt(
        messages,
        individual_name,
        physical_description,
        api_key=key,
    )

    # Step 2: Load portrait image if it exists
    portrait_image = None
    if portrait_path and Path(portrait_path).exists():
        logger.info("Using self-portrait as character reference: %s", portrait_path)
        portrait_bytes = Path(portrait_path).read_bytes()
        portrait_image = types.Image(
            image_bytes=portrait_bytes,
            mime_type="image/png",
        )

    # Step 3: Call Veo
    client = genai.Client(api_key=key)
    logger.info("Calling Veo (%s) — prompt: %s", veo_model, scene_prompt[:80])

    veo_config = types.GenerateVideosConfig(
        aspect_ratio=aspect_ratio,
        person_generation=person_generation,
        negative_prompt=("cartoon, anime, drawing, low quality, blurry, watermark, text overlay, subtitles"),
    )

    generate_kwargs: dict[str, Any] = {
        "model": veo_model,
        "prompt": scene_prompt,
        "config": veo_config,
    }
    # Use the self-portrait as the starting frame so the video
    # begins from the character's face and animates from there
    if portrait_image is not None:
        generate_kwargs["image"] = portrait_image

    operation = client.models.generate_videos(**generate_kwargs)

    # Step 4: Poll until done
    elapsed = 0
    while not operation.done:
        if elapsed >= MAX_POLL_SECONDS:
            logger.error("Video generation timed out after %ds", elapsed)
            return None
        logger.info("Waiting for video generation... (%ds elapsed)", elapsed)
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        operation = client.operations.get(operation)

    # Step 5: Download and save
    if not operation.response or not operation.response.generated_videos:
        logger.error("Veo returned no generated videos")
        return None

    generated_video = operation.response.generated_videos[0]
    if generated_video.video is None:
        logger.error("Veo returned a generated video entry with no video file")
        return None
    client.files.download(file=generated_video.video)

    # Determine output path
    if output_path is None:
        storage_path = os.environ.get("PERSONAUT_STORAGE_PATH", "./data/personaut.db")
        data_dir = Path(storage_path).resolve().parent
        videos_dir = data_dir / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{session_id or 'video'}_{int(time.time())}.mp4"
        output_path = str(videos_dir / filename)

    generated_video.video.save(output_path)
    logger.info("Video saved to %s", output_path)

    # Return the relative URL for serving
    fname = Path(output_path).name
    return f"/data/videos/{fname}"
