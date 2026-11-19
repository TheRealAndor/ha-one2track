"""Tests for the One2Track config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.one2track.api import (
    One2TrackApiClientAuthenticationError,
    One2TrackApiClientCommunicationError,
    One2TrackApiClientError,
)
from custom_components.one2track.const import DOMAIN

from .conftest import ACCOUNT_ID

USER_INPUT = {CONF_USERNAME: "sam", CONF_PASSWORD: "secret"}

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


def _entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=ACCOUNT_ID, data=USER_INPUT, title="One2Track (sam)"
    )
    entry.add_to_hass(hass)
    return entry


async def test_user_flow(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """A valid login creates an entry with the account ID as unique ID."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "One2Track (sam)"
    assert result["data"] == USER_INPUT
    assert result["result"].unique_id == ACCOUNT_ID
    mock_client.async_discover_devices.assert_awaited_once()


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (One2TrackApiClientAuthenticationError("bad"), "auth"),
        (One2TrackApiClientCommunicationError("down"), "connection"),
        (One2TrackApiClientError("odd"), "unknown"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_user_flow_errors_recover(
    hass: HomeAssistant,
    mock_client: MagicMock,
    side_effect: Exception,
    error: str,
) -> None:
    """A failed login shows the error and can be retried."""
    mock_client.async_authenticate.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_client.async_authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_device_discovery_fails(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Login works but the watches cannot be read: connection error."""
    mock_client.async_discover_devices.side_effect = (
        One2TrackApiClientCommunicationError("down")
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "connection"}


async def test_user_flow_already_configured(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """The same One2Track account cannot be added twice."""
    _entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_flow(hass: HomeAssistant, mock_client: MagicMock) -> None:
    """Re-authentication stores the new password and reloads the entry."""
    entry = _entry(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["description_placeholders"]["username"] == "sam"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-secret"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == {CONF_USERNAME: "sam", CONF_PASSWORD: "new-secret"}


async def test_reauth_flow_error_recovers(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """A wrong password during re-authentication shows an error and can be retried."""
    entry = _entry(hass)
    mock_client.async_authenticate.side_effect = (
        One2TrackApiClientAuthenticationError("bad")
    )
    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "wrong"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "auth"}
    assert entry.data[CONF_PASSWORD] == "secret"

    mock_client.async_authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-secret"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"


async def test_reauth_flow_wrong_account(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Credentials of another One2Track account are refused."""
    entry = _entry(hass)
    mock_client.async_authenticate.return_value = "99999"
    result = await entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "other"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_account"
    assert entry.data[CONF_PASSWORD] == "secret"
