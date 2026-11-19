"""Tests for setting up the One2Track integration and its actions."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.setup import async_setup_component

from custom_components.one2track.const import DOMAIN
from custom_components.one2track.services import ALL_SERVICES


async def test_actions_registered_without_entry(hass: HomeAssistant) -> None:
    """All actions exist as soon as the integration loads, even without an account."""
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    for service in ALL_SERVICES:
        assert hass.services.has_service(DOMAIN, service), service


async def test_action_for_unknown_watch_is_refused(hass: HomeAssistant) -> None:
    """An action for something that is not a One2Track watch raises a validation error."""
    assert await async_setup_component(hass, DOMAIN, {})
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "force_update",
            {"entity_id": "device_tracker.unknown"},
            blocking=True,
        )
