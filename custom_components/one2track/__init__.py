"""The One2Track integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    One2TrackApiClient,
    One2TrackApiClientAuthenticationError,
    One2TrackApiClientCommunicationError,
)
from .const import DOMAIN, LOGGER
from .coordinator import One2TrackCoordinator
from .data import One2TrackData
from .services import async_setup_services

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

    from .data import One2TrackConfigEntry

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.SELECT,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:  # noqa: ARG001
    """Register the One2Track actions once, independent of config entries."""
    async_setup_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: One2TrackConfigEntry,
) -> bool:
    """Set up One2Track from a config entry."""
    client = One2TrackApiClient(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=async_create_clientsession(hass),
    )

    try:
        await client.async_authenticate()
    except One2TrackApiClientAuthenticationError as exc:
        raise ConfigEntryAuthFailed(
            f"Unable to log in to One2Track: {exc}"
        ) from exc
    except One2TrackApiClientCommunicationError as exc:
        raise ConfigEntryNotReady(
            f"Unable to connect to One2Track: {exc}"
        ) from exc

    coordinator = One2TrackCoordinator(hass, client)

    try:
        await coordinator.async_setup()
    except One2TrackApiClientAuthenticationError as exc:
        raise ConfigEntryAuthFailed(
            f"Unable to log in to One2Track: {exc}"
        ) from exc
    except One2TrackApiClientCommunicationError as exc:
        raise ConfigEntryNotReady(
            f"Unable to set up devices: {exc}"
        ) from exc

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = One2TrackData(
        client=client,
        coordinator=coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: One2TrackConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: One2TrackConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
