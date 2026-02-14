"""Tests for LiveInteractionServer and LiveInteractionClient."""

from __future__ import annotations

from unittest.mock import MagicMock


class MockIndividual:
    """Mock individual for testing."""

    def __init__(self, id: str = "ind_mock", name: str = "Mock") -> None:
        self.id = id
        self.name = name


class MockSituation:
    """Mock situation for testing."""

    def __init__(self, id: str = "sit_mock", description: str = "Mock situation") -> None:
        self.id = id
        self.description = description


class MockRelationship:
    """Mock relationship for testing."""

    def __init__(self, id: str = "rel_mock") -> None:
        self.id = id


class TestLiveInteractionServer:
    """Tests for LiveInteractionServer."""

    def test_create_server(self) -> None:
        """Test creating server."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        assert server.individuals == {}
        assert server.situations == {}
        assert server.relationships == {}

    def test_create_server_with_config(self) -> None:
        """Test creating server with config."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer(config={"debug": True})
        assert server.config == {"debug": True}

    def test_add_individual(self) -> None:
        """Test adding individual."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        individual = MockIndividual()

        ind_id = server.add_individual(individual)
        assert ind_id == "ind_mock"
        assert server.individuals["ind_mock"] == individual

    def test_add_individual_with_override(self) -> None:
        """Test adding individual with ID override."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        individual = MockIndividual()

        ind_id = server.add_individual(individual, id_override="custom_id")
        assert ind_id == "custom_id"
        assert "custom_id" in server.individuals

    def test_add_individual_generates_id(self) -> None:
        """Test adding individual without ID generates one."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()

        class NoIdIndividual:
            pass

        ind_id = server.add_individual(NoIdIndividual())
        assert ind_id.startswith("ind_")

    def test_add_situation(self) -> None:
        """Test adding situation."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        situation = MockSituation()

        sit_id = server.add_situation(situation)
        assert sit_id == "sit_mock"
        assert server.situations["sit_mock"] == situation

    def test_add_relationship(self) -> None:
        """Test adding relationship."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        relationship = MockRelationship()

        rel_id = server.add_relationship(relationship)
        assert rel_id == "rel_mock"
        assert server.relationships["rel_mock"] == relationship

    def test_is_running_initially_false(self) -> None:
        """Test is_running is false initially."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        assert server.is_running() is False

    def test_get_api_url(self) -> None:
        """Test getting API URL."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        url = server.get_api_url(port=8000)
        assert url == "http://127.0.0.1:8000/api"

    def test_get_api_url_custom_host(self) -> None:
        """Test getting API URL with custom host."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        url = server.get_api_url(port=9000, host="0.0.0.0")
        assert url == "http://0.0.0.0:9000/api"

    def test_get_ui_url(self) -> None:
        """Test getting UI URL."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        url = server.get_ui_url(port=5000)
        assert url == "http://127.0.0.1:5000"

    def test_stop_sets_running_false(self) -> None:
        """Test stop sets running to false."""
        from personaut.server import LiveInteractionServer

        server = LiveInteractionServer()
        server._running = True
        server.stop()
        assert server.is_running() is False


class TestLiveInteractionClient:
    """Tests for LiveInteractionClient."""

    def test_create_client(self) -> None:
        """Test creating client."""
        from personaut.server import LiveInteractionClient

        client = LiveInteractionClient()
        assert client.base_url == "http://localhost:8000/api"

    def test_create_client_custom_url(self) -> None:
        """Test creating client with custom URL."""
        from personaut.server import LiveInteractionClient

        client = LiveInteractionClient("http://example.com:9000/api/")
        # Should strip trailing slash
        assert client.base_url == "http://example.com:9000/api"

    def test_close_client(self) -> None:
        """Test closing client."""
        from personaut.server import LiveInteractionClient

        client = LiveInteractionClient()
        client._session = MagicMock()
        client.close()
        assert client._session is None


class TestServerPackageExports:
    """Tests for server package exports."""

    def test_exports_server(self) -> None:
        """Test server is exported."""
        from personaut.server import LiveInteractionServer

        assert LiveInteractionServer is not None

    def test_exports_client(self) -> None:
        """Test client is exported."""
        from personaut.server import LiveInteractionClient

        assert LiveInteractionClient is not None
