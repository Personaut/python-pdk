"""Tests for images/portrait.py and images/video.py."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from personaut.images.portrait import (
    build_portrait_prompt,
    generate_portrait,
    save_portrait,
)
from personaut.individuals.physical import PhysicalFeatures


class TestBuildPortraitPrompt:
    """Tests for build_portrait_prompt."""

    def test_basic_prompt(self) -> None:
        """Should produce a prompt with basic features."""
        features = PhysicalFeatures(hair="short dark hair", eyes="brown")
        prompt = build_portrait_prompt(features)
        assert "short dark hair" in prompt
        assert "brown" in prompt
        assert "portrait" in prompt.lower()

    def test_all_features(self) -> None:
        """Should include all populated features."""
        features = PhysicalFeatures(
            age_appearance="mid-30s",
            build="athletic",
            height="6'1\"",
            skin_tone="olive",
            hair="dark curly hair",
            eyes="green",
            facial_features="strong jawline",
            clothing_style="casual",
        )
        prompt = build_portrait_prompt(features)
        assert "mid-30s" in prompt
        assert "athletic" in prompt
        assert "6'1\"" in prompt
        assert "olive" in prompt
        assert "dark curly" in prompt
        assert "green" in prompt
        assert "strong jawline" in prompt
        assert "casual" in prompt

    def test_distinguishing_features_visible(self) -> None:
        """Should include visible distinguishing features."""
        features = PhysicalFeatures(
            distinguishing_features=["scar on left cheek", "wears a ring"],
        )
        prompt = build_portrait_prompt(features)
        assert "scar on left cheek" in prompt

    def test_distinguishing_features_non_visible(self) -> None:
        """Should filter out non-visible features."""
        features = PhysicalFeatures(
            distinguishing_features=["deep voice", "strong handshake"],
        )
        prompt = build_portrait_prompt(features)
        assert "deep voice" not in prompt
        assert "strong handshake" not in prompt

    def test_accessories_wearable(self) -> None:
        """Should include wearable accessories."""
        features = PhysicalFeatures(
            accessories=["round glasses", "silver necklace"],
        )
        prompt = build_portrait_prompt(features)
        assert "round glasses" in prompt
        assert "silver necklace" in prompt

    def test_accessories_non_wearable(self) -> None:
        """Should filter out non-wearable accessories."""
        features = PhysicalFeatures(
            accessories=["phone", "laptop bag"],
        )
        prompt = build_portrait_prompt(features)
        assert "phone" not in prompt

    def test_empty_features(self) -> None:
        """Even empty features should produce a valid prompt."""
        features = PhysicalFeatures()
        prompt = build_portrait_prompt(features)
        assert "A person" in prompt

    def test_no_age_appearance(self) -> None:
        """Without age, should use generic 'A person'."""
        features = PhysicalFeatures(hair="blonde")
        prompt = build_portrait_prompt(features)
        assert "A person" in prompt


class TestGeneratePortrait:
    """Tests for generate_portrait (early-return paths)."""

    def test_empty_features_returns_none(self) -> None:
        """Should return None for empty features."""
        features = PhysicalFeatures()
        result = generate_portrait(features)
        assert result is None

    def test_no_api_key_returns_none(self) -> None:
        """Should return None when no API key is available."""
        features = PhysicalFeatures(hair="dark", eyes="brown")
        env = {k: v for k, v in os.environ.items() if k != "GOOGLE_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            result = generate_portrait(features)
            assert result is None


class TestSavePortrait:
    """Tests for save_portrait."""

    def test_save_to_custom_dir(self, tmp_path: Path) -> None:
        """Should save file to custom directory."""
        image_bytes = b"fake-png-data"
        result = save_portrait(image_bytes, "ind_123", output_dir=str(tmp_path))
        assert result == "/data/portraits/ind_123.png"
        saved_file = tmp_path / "ind_123.png"
        assert saved_file.exists()
        assert saved_file.read_bytes() == b"fake-png-data"

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Should create output directory if needed."""
        output_dir = tmp_path / "new" / "dir"
        save_portrait(b"data", "ind_456", output_dir=str(output_dir))
        assert (output_dir / "ind_456.png").exists()

    def test_save_default_dir(self) -> None:
        """Default dir should resolve to data dir/portraits/."""
        import os

        # Point to a temp-like data dir so we don't pollute
        data_dir = Path(__file__).resolve().parent / "_test_data"
        with patch.dict(os.environ, {"PERSONAUT_STORAGE_PATH": str(data_dir / "personaut.db")}):
            result = save_portrait(b"test-data", "ind_default")
        assert result == "/data/portraits/ind_default.png"
        # Clean up
        created_file = data_dir / "portraits" / "ind_default.png"
        if created_file.exists():
            created_file.unlink()
        # Remove empty dirs
        portraits_dir = data_dir / "portraits"
        if portraits_dir.exists() and not any(portraits_dir.iterdir()):
            portraits_dir.rmdir()
        if data_dir.exists() and not any(data_dir.iterdir()):
            data_dir.rmdir()
