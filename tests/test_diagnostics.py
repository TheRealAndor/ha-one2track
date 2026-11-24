"""Tests for the diagnostics download: useful data in, personal data out."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.one2track.const import DOMAIN
from custom_components.one2track.diagnostics import (
    async_get_config_entry_diagnostics,
    async_get_device_diagnostics,
)

UUID = "0f0f0f0f-1111-2222-3333-444444444444"
PERSONAL = [
    "sam@example.com",
    "secret",
    UUID,
    "Sam",
    "0612345678",
    "SN123456",
    "Dorpsstraat 1",
    "52.1234",
    "5.6789",
    "8931000000000000000",
]

DEVICE_DATA = {
    "uuid": UUID,
    "name": "Sam",
    "serial_number": "SN123456",
    "phone_number": "0612345678",
    "device_model_id": 377,
    "model_name": "Connect YOU",
    "status": "GPS",
    "avatar": {"url": "/avatar.png"},
    "simcard": {"balance_cents": 450, "tariff_type": "prepaid", "iccid": "8931000000000000000"},
    "last_location": {
        "address": "Dorpsstraat 1",
        "latitude": "52.1234",
        "longitude": "5.6789",
        "battery_percentage": 80,
        "meta_data": {"steps": "1200", "stations": [{"cid": "1"}]},
    },
}


def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={CONF_USERNAME: "sam@example.com", CONF_PASSWORD: "secret"},
    )
    entry.add_to_hass(hass)
    coordinator = MagicMock()
    coordinator.device_list = [{"uuid": UUID}]
    coordinator.get_device_data.return_value = DEVICE_DATA
    coordinator.get_capabilities.return_value = {"functions": {"0078": "GPS tracking"}}
    coordinator.is_settings_synced.return_value = True
    coordinator.get_phonebook.return_value = [{"name": "Mama", "number": "0611111111"}]
    coordinator.get_whitelist.return_value = ["0622222222"]
    coordinator.get_alarms.return_value = ["07:00-1-1"]
    coordinator.get_quiet_times.return_value = [{"start": "08:30", "end": "12:00"}]
    coordinator.last_update_success = True
    coordinator.update_interval = timedelta(seconds=60)
    entry.runtime_data = MagicMock(coordinator=coordinator)
    return entry


async def test_config_entry_diagnostics(hass: HomeAssistant) -> None:
    """The account diagnostics keep the model and state, but no personal data."""
    entry = _setup(hass)
    result = await async_get_config_entry_diagnostics(hass, entry)

    text = str(result)
    for value in PERSONAL:
        assert value not in text, value
    assert "0611111111" not in text
    assert "0622222222" not in text

    watch = result["watches"][0]
    assert watch["model_name"] == "Connect YOU"
    assert watch["device_model_id"] == 377
    assert watch["data"]["simcard"] == {"balance_cents": 450, "tariff_type": "prepaid"}
    assert watch["data"]["last_location"]["battery_percentage"] == 80
    assert watch["settings"]["phonebook_contacts"] == 1
    assert watch["settings"]["whitelist_numbers"] == 1
    assert watch["capabilities"] == {"functions": {"0078": "GPS tracking"}}
    assert result["coordinator"] == {
        "last_update_success": True,
        "update_interval": "0:01:00",
        "watches": 1,
    }


async def test_device_diagnostics(hass: HomeAssistant) -> None:
    """The diagnostics of one watch are redacted the same way."""
    entry = _setup(hass)
    device = MagicMock(identifiers={(DOMAIN, UUID)})
    result = await async_get_device_diagnostics(hass, entry, device)
    assert result["watch"]["model_name"] == "Connect YOU"
    for value in PERSONAL:
        assert value not in str(result), value

    other = MagicMock(identifiers={("other", "x")})
    assert (await async_get_device_diagnostics(hass, entry, other))["watch"] is None
