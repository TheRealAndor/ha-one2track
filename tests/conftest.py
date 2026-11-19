"""Shared fixtures for the One2Track tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"

ACCOUNT_ID = "12345"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load custom_components/one2track in every test."""


@pytest.fixture
def mock_client() -> Generator[MagicMock]:
    """Patch the API client used by the config flow."""
    with patch(
        "custom_components.one2track.config_flow.One2TrackApiClient", autospec=True
    ) as client_cls:
        client = client_cls.return_value
        client.async_authenticate = AsyncMock(return_value=ACCOUNT_ID)
        client.async_discover_devices = AsyncMock(return_value=[])
        yield client


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Skip setting up the integration after the flow creates or reloads an entry."""
    with patch(
        "custom_components.one2track.async_setup_entry", return_value=True
    ) as setup_entry:
        yield setup_entry
