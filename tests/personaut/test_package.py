"""Placeholder test to verify test infrastructure works."""

from __future__ import annotations

import personaut


class TestPackageImport:
    """Tests for package import and version."""

    def test_import_package(self) -> None:
        """Package should be importable."""
        assert personaut is not None

    def test_version_exists(self) -> None:
        """Package should have a version string."""
        assert hasattr(personaut, "__version__")
        assert isinstance(personaut.__version__, str)
        assert personaut.__version__ == "0.3.2"
