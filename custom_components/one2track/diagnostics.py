"""Diagnostics for the One2Track integration.

Download it from the integration or device page and attach it to an issue.
Personal data (names, phone numbers, location, serial numbers, account IDs,
contacts) is redacted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.device_registry import DeviceEntry

    from .coordinator import One2TrackCoordinator
    from .data import One2TrackConfigEntry

TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    # Identity of the child and the account
    "name",
    "uuid",
    "id",
    "account_id",
    "user_id",
    "model_user_id",
    "legacy_device_id",
    "serial_number",
    "avatar",
    "legacy_avatar",
    # Phone numbers and contacts
    "phone_number",
    "PHONEBOOK",
    # Location
    "address",
    "latitude",
    "longitude",
    "altitude",
    "stations",
    "routers",
}

# Only these SIM card fields are kept; the rest (number, ICCID, ...) is dropped.
SIMCARD_KEEP = {"balance_cents", "tariff_type"}


def _watch_diagnostics(coordinator: One2TrackCoordinator, uuid: str) -> dict[str, Any]:
    """Return the redacted state of one watch."""
    data = dict(coordinator.get_device_data(uuid))
    if isinstance(simcard := data.get("simcard"), dict):
        data["simcard"] = {k: v for k, v in simcard.items() if k in SIMCARD_KEEP}
    return {
        "model_name": data.get("model_name"),
        "device_model_id": data.get("device_model_id"),
        "data": async_redact_data(data, TO_REDACT),
        "capabilities": coordinator.get_capabilities(uuid),
        "settings": {
            "synced": coordinator.is_settings_synced(uuid),
            "phonebook_contacts": len(coordinator.get_phonebook(uuid)),
            "whitelist_numbers": len(coordinator.get_whitelist(uuid)),
            "alarms": coordinator.get_alarms(uuid),
            "quiet_times": coordinator.get_quiet_times(uuid),
        },
    }


def _coordinator_diagnostics(coordinator: One2TrackCoordinator) -> dict[str, Any]:
    return {
        "last_update_success": coordinator.last_update_success,
        "update_interval": str(coordinator.update_interval),
        "watches": len(coordinator.device_list),
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: One2TrackConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a One2Track account."""
    coordinator = entry.runtime_data.coordinator
    return {
        "entry": {
            "version": entry.version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
        },
        "coordinator": _coordinator_diagnostics(coordinator),
        "watches": [
            _watch_diagnostics(coordinator, device["uuid"])
            for device in coordinator.device_list
        ],
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    entry: One2TrackConfigEntry,
    device: DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for one watch."""
    coordinator = entry.runtime_data.coordinator
    uuid = next(
        (ident for domain, ident in device.identifiers if domain == entry.domain), None
    )
    return {
        "coordinator": _coordinator_diagnostics(coordinator),
        "watch": _watch_diagnostics(coordinator, uuid) if uuid else None,
    }
