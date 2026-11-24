"""DataUpdateCoordinator for the One2Track integration."""

from __future__ import annotations

import asyncio
import re
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    One2TrackApiClientAuthenticationError,
    One2TrackApiClientError,
)
from .const import (
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    LOGGER,
    PHONEBOOK_CODES,
    QUIET_TIMES_CODES,
    RADIO_COMMANDS,
    ALARM_CODES,
    WHITELIST_SLOT_CODES,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .api import One2TrackApiClient
    from .data import One2TrackConfigEntry

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.settings"


class One2TrackCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator that polls device state from One2Track.

    Data structure: {uuid: {"device": {...}, "last_location": {...}}}
    The initial device list (from JSON endpoint) is stored separately for
    discovery metadata (serial_number, name, simcard, etc.).
    Per-device capabilities (supported commands and options) are discovered
    at setup and stored for entity creation.
    """

    config_entry: One2TrackConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: One2TrackApiClient,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name="One2Track",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
            always_update=False,
        )
        self.client = client
        self._device_list: list[dict[str, Any]] = []
        # Per-device capabilities: {uuid: {"functions": {...}, "options": {...}}}
        self._capabilities: dict[str, dict[str, Any]] = {}
        # Per-device settings (synced from portal on startup, updated by services)
        self._phonebook: dict[str, list[dict[str, str]]] = {}
        self._whitelist: dict[str, list[str]] = {}
        self._alarms: dict[str, list[str]] = {}
        self._quiet_times: dict[str, list[dict[str, str]]] = {}
        # Track which devices have synced settings (vs. unknown state)
        self._settings_synced: dict[str, bool] = {}
        # Newest portal message seen per device: {uuid: {"last": "YYYY-MM-DD HH:MM",
        # "keys": [...]}}. Messages have no ID, so anything newer than "last", or
        # at "last" with an unseen key, is new. Missing uuid = not seeded yet.
        self._message_marks: dict[str, dict[str, Any]] = {}
        # Persistent storage for settings across HA restarts
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    @property
    def device_list(self) -> list[dict[str, Any]]:
        """Return the initial device list (from JSON discovery)."""
        return self._device_list

    def get_capabilities(self, uuid: str) -> dict[str, Any]:
        """Return discovered capabilities for a device.

        Returns {"functions": {code: label, ...}, "options": {code: [...], ...}}
        """
        return self._capabilities.get(uuid, {"functions": {}, "options": {}})

    def device_supports(self, uuid: str, cmd_code: str) -> bool:
        """Check if a device supports a given command code."""
        caps = self.get_capabilities(uuid)
        return cmd_code in caps.get("functions", {})

    def device_find_code(self, uuid: str, candidates: tuple[str, ...]) -> str | None:
        """Find which of several candidate command codes this device supports.

        Used for model-specific commands (GPS interval: 0077 or 0078, etc.)
        Returns the first matching code, or None.
        """
        caps = self.get_capabilities(uuid)
        funcs = caps.get("functions", {})
        for code in candidates:
            if code in funcs:
                return code
        return None

    def get_command_options(self, uuid: str, cmd_code: str) -> list[dict[str, Any]]:
        """Return discovered options for a command on a device."""
        caps = self.get_capabilities(uuid)
        return caps.get("options", {}).get(cmd_code, [])

    # ── Settings state (synced from portal, updated by services) ───

    def is_settings_synced(self, uuid: str) -> bool:
        """Check if we have synced settings for a device."""
        return self._settings_synced.get(uuid, False)

    def get_phonebook(self, uuid: str) -> list[dict[str, str]]:
        """Return last-known phonebook contacts for a device."""
        return list(self._phonebook.get(uuid, []))

    def set_phonebook(self, uuid: str, contacts: list[dict[str, str]]) -> None:
        """Store phonebook contacts locally and persist."""
        self._phonebook[uuid] = list(contacts)
        self._settings_synced[uuid] = True
        self.hass.async_create_task(self._async_save_settings())
        self.async_update_listeners()

    def get_whitelist(self, uuid: str) -> list[str]:
        """Return last-known whitelist numbers for a device."""
        return list(self._whitelist.get(uuid, []))

    def set_whitelist(self, uuid: str, numbers: list[str]) -> None:
        """Store whitelist numbers locally and persist."""
        self._whitelist[uuid] = [n for n in numbers if n]
        self._settings_synced[uuid] = True
        self.hass.async_create_task(self._async_save_settings())
        self.async_update_listeners()

    def get_alarms(self, uuid: str) -> list[str]:
        """Return last-known alarm settings for a device."""
        return list(self._alarms.get(uuid, []))

    def set_alarms(self, uuid: str, alarms: list[str]) -> None:
        """Store alarm settings locally and persist."""
        self._alarms[uuid] = list(alarms)
        self._settings_synced[uuid] = True
        self.hass.async_create_task(self._async_save_settings())
        self.async_update_listeners()

    def get_quiet_times(self, uuid: str) -> list[dict[str, str]]:
        """Return last-known quiet time windows for a device."""
        return list(self._quiet_times.get(uuid, []))

    def set_quiet_times(self, uuid: str, windows: list[dict[str, str]]) -> None:
        """Store quiet time windows locally and persist."""
        self._quiet_times[uuid] = list(windows)
        self._settings_synced[uuid] = True
        self.hass.async_create_task(self._async_save_settings())
        self.async_update_listeners()

    # ── Persistent storage ────────────────────────────────────────────

    async def _async_save_settings(self) -> None:
        """Persist settings to disk."""
        await self._store.async_save({
            "phonebook": self._phonebook,
            "whitelist": self._whitelist,
            "alarms": self._alarms,
            "quiet_times": self._quiet_times,
            "synced": self._settings_synced,
            "message_marks": self._message_marks,
        })

    async def _async_load_settings(self) -> None:
        """Load settings from disk (fallback when portal readback fails)."""
        data = await self._store.async_load()
        if not data:
            return
        self._phonebook = data.get("phonebook", {})
        self._whitelist = data.get("whitelist", {})
        self._alarms = data.get("alarms", {})
        self._quiet_times = data.get("quiet_times", {})
        self._settings_synced = data.get("synced", {})
        self._message_marks = data.get("message_marks", {})
        LOGGER.debug("Loaded persisted settings for %d devices", len(self._settings_synced))

    # ── Portal readback (best-effort sync of current settings) ────────

    async def _async_sync_device_settings(self, uuid: str) -> None:
        """Try to read current phonebook/whitelist/alarms/quiet times from portal.

        The function form pages contain <input> fields with current values.
        This is best-effort — if parsing fails we keep persisted state.
        """
        synced_any = False

        # Phonebook: find which code this device uses, values are name/number pairs
        pb_code = self.device_find_code(uuid, PHONEBOOK_CODES)
        if pb_code:
            try:
                values = await self.client.async_fetch_form_values(uuid, pb_code)
                if values and len(values) >= 2:
                    contacts = []
                    for i in range(0, len(values) - 1, 2):
                        name, number = values[i], values[i + 1]
                        if name or number:
                            contacts.append({"name": name, "number": number})
                    self._phonebook[uuid] = contacts
                    synced_any = True
                    LOGGER.debug("Synced %d phonebook contacts for %s", len(contacts), uuid)
            except Exception:  # noqa: BLE001
                LOGGER.debug("Could not sync phonebook for %s", uuid)

        # Whitelist: find which slot pair this device uses
        for slot1, slot2 in WHITELIST_SLOT_CODES:
            if self.device_supports(uuid, slot1):
                try:
                    vals1 = await self.client.async_fetch_form_values(uuid, slot1)
                    vals2 = await self.client.async_fetch_form_values(uuid, slot2)
                    all_numbers = [n for n in (vals1 + vals2) if n]
                    self._whitelist[uuid] = all_numbers
                    synced_any = True
                    LOGGER.debug("Synced %d whitelist numbers for %s", len(all_numbers), uuid)
                except Exception:  # noqa: BLE001
                    LOGGER.debug("Could not sync whitelist for %s", uuid)
                break

        # Alarms: find which code this device uses
        alarm_code = self.device_find_code(uuid, ALARM_CODES)
        if alarm_code:
            try:
                values = await self.client.async_fetch_form_values(uuid, alarm_code)
                if values:
                    # Validate alarm values — the portal sometimes returns raw
                    # JavaScript fragments (e.g. "' + time + '-0-1'") instead
                    # of rendered values like "07:00-1-2". Only accept values
                    # that match the expected HH:MM-... format.
                    valid_alarms = [
                        v for v in values
                        if v and re.match(r"^\d{2}:\d{2}-", v)
                    ]
                    if valid_alarms:
                        self._alarms[uuid] = valid_alarms
                        synced_any = True
                        LOGGER.debug("Synced %d alarms for %s", len(valid_alarms), uuid)
                    elif all("' +" in v or "+ '" in v for v in values if v):
                        # Only the portal's JavaScript row template, i.e. no
                        # alarms are set on the watch: nothing to sync.
                        LOGGER.debug("No alarms set in the portal for %s", uuid)
                    elif values:
                        LOGGER.warning(
                            "Alarm values from portal for %s appear malformed "
                            "(got %r), keeping local state",
                            uuid, values,
                        )
            except Exception:  # noqa: BLE001
                LOGGER.debug("Could not sync alarms for %s", uuid)

        # Quiet times: find which code this device uses
        qt_code = self.device_find_code(uuid, QUIET_TIMES_CODES)
        if qt_code:
            try:
                values = await self.client.async_fetch_form_values(uuid, qt_code)
                if values:
                    windows = []
                    for v in values:
                        parts = v.split(",")
                        if len(parts) >= 3 and parts[0] == "1":
                            start_raw = parts[1]
                            end_raw = parts[2]
                            start = f"{start_raw[:2]}:{start_raw[2:]}" if len(start_raw) == 4 else start_raw
                            end = f"{end_raw[:2]}:{end_raw[2:]}" if len(end_raw) == 4 else end_raw
                            windows.append({"start": start, "end": end})
                    self._quiet_times[uuid] = windows
                    synced_any = True
                    LOGGER.debug("Synced %d quiet times for %s", len(windows), uuid)
            except Exception:  # noqa: BLE001
                LOGGER.debug("Could not sync quiet times for %s", uuid)

        if synced_any:
            self._settings_synced[uuid] = True

    async def async_refresh_settings(self, uuid: str) -> None:
        """Re-read current settings from the portal.

        Call this before modifying settings (add/remove operations) to ensure
        the local state reflects any changes made via the app or website.
        """
        await self._async_sync_device_settings(uuid)

    # ── Portal messages ───────────────────────────────────────────────

    def get_new_messages(self, uuid: str) -> list[dict[str, str]]:
        """Return the messages that arrived in the last update."""
        if not self.data:
            return []
        return list(self.data.get(uuid, {}).get("new_messages", []))

    async def _async_fetch_new_messages(self, uuid: str) -> list[dict[str, str]]:
        """Fetch portal messages and return the ones not seen before.

        On the first run for a device, existing messages are only marked as
        seen, so installing the integration does not replay old alerts.
        """
        try:
            messages = await self.client.async_get_messages(uuid)
        except One2TrackApiClientError as exc:
            LOGGER.debug("Could not fetch messages for %s: %s", uuid, exc)
            return []
        # Only messages from the watch; "rtl" are the ones sent from the portal
        messages = [msg for msg in messages if msg["direction"] != "rtl"]

        def stamp(msg: dict[str, str]) -> str:
            return f"{msg['date']} {msg['time']}"

        def key(msg: dict[str, str]) -> str:
            return f"{msg['direction']}|{msg['sender']}|{msg['text']}"

        mark = self._message_marks.get(uuid)
        last = mark["last"] if mark else ""
        seen_keys = set(mark["keys"]) if mark else set()

        new = [] if mark is None else [
            msg for msg in messages
            if stamp(msg) > last or (stamp(msg) == last and key(msg) not in seen_keys)
        ]

        newest = max((stamp(msg) for msg in messages), default=last)
        keys = {key(msg) for msg in messages if stamp(msg) == newest}
        if newest == last:
            keys |= seen_keys
        new_mark = {"last": newest, "keys": sorted(keys)}
        if new_mark != mark:
            self._message_marks[uuid] = new_mark
            self.hass.async_create_task(self._async_save_settings())

        if new:
            LOGGER.debug("%d new message(s) for %s", len(new), uuid)
        return new

    # ── Setup ─────────────────────────────────────────────────────────

    async def async_setup(self) -> None:
        """Discover devices and their capabilities during initial setup."""
        self._device_list = await self.client.async_discover_devices()

        # Load persisted settings first (fast fallback)
        await self._async_load_settings()

        # Discover capabilities for each device
        for dev in self._device_list:
            uuid = dev.get("uuid", "")
            if not uuid:
                continue
            try:
                caps = await self.client.async_discover_capabilities(uuid)

                # For commands with radio-button options, discover the options
                functions = caps.get("functions", {})
                options: dict[str, list] = {}
                for code in RADIO_COMMANDS:
                    if code in functions:
                        opts = await self.client.async_discover_command_options(
                            uuid, code
                        )
                        if opts:
                            options[code] = opts
                caps["options"] = options

                self._capabilities[uuid] = caps
                LOGGER.info(
                    "Device %s (%s): %d commands, options for %s",
                    dev.get("name", uuid),
                    uuid,
                    len(functions),
                    list(options.keys()),
                )
            except One2TrackApiClientError as exc:
                LOGGER.warning(
                    "Could not discover capabilities for %s: %s", uuid, exc
                )
                self._capabilities[uuid] = {"functions": {}, "options": {}}

            # Try to sync settings from portal (best-effort, overwrites stored)
            try:
                await self._async_sync_device_settings(uuid)
            except Exception:  # noqa: BLE001
                LOGGER.debug("Settings sync failed for %s, using stored state", uuid)

        # Persist whatever we synced
        await self._async_save_settings()

    def get_device_data(self, uuid: str) -> dict[str, Any]:
        """Get merged device data for a UUID.

        Merges the initial JSON discovery data with the scraped HTML data.
        The HTML-scraped data takes precedence for overlapping fields.
        """
        base: dict[str, Any] = {}
        for dev in self._device_list:
            if dev.get("uuid") == uuid:
                base = dict(dev)
                break

        if self.data and uuid in self.data:
            scraped = self.data[uuid]
            if "device" in scraped:
                base.update(scraped["device"])
            if "last_location" in scraped:
                base["last_location"] = scraped["last_location"]
            if scraped.get("model_name"):
                base["model_name"] = scraped["model_name"]

        return base

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch device states from One2Track.

        Refreshes both the JSON device list (for base data like battery,
        timestamps, simcard) and the HTML-scraped data (for richer fields).
        Even if HTML scraping fails, entities stay fresh via the JSON data.
        """
        try:
            async with asyncio.timeout(60):
                # Refresh base device data from JSON API. An auth error here
                # usually means the session expired, not that the password is
                # wrong: log in again once, and only a failed login counts.
                try:
                    try:
                        self._device_list = await self.client.async_discover_devices()
                    except One2TrackApiClientAuthenticationError:
                        LOGGER.debug("Session expired, logging in again")
                        await self.client.async_authenticate()
                        self._device_list = await self.client.async_discover_devices()
                except One2TrackApiClientAuthenticationError:
                    raise
                except One2TrackApiClientError:
                    LOGGER.debug("JSON device refresh failed, keeping cached list")

                # Scrape HTML for additional detail per device
                states = await self.client.async_get_all_device_states()

                # New portal messages per device (best-effort). Part of the
                # data so listeners are notified when messages arrive.
                for dev in self._device_list:
                    uuid = dev.get("uuid", "")
                    if uuid:
                        states.setdefault(uuid, {})["new_messages"] = (
                            await self._async_fetch_new_messages(uuid)
                        )
                return states
        except One2TrackApiClientAuthenticationError as exc:
            raise ConfigEntryAuthFailed(exc) from exc
        except One2TrackApiClientError as exc:
            raise UpdateFailed(exc) from exc
