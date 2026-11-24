"""Event platform for One2Track: messages from the portal's Messages tab."""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.components.event import EventEntity
from homeassistant.core import callback
from homeassistant.util import dt as dt_util

from .entity import One2TrackEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import One2TrackConfigEntry

# Read-only, data comes from the coordinator
PARALLEL_UPDATES = 0

EVENT_LOW_BATTERY = "low_battery"
EVENT_SOS = "sos"
EVENT_MESSAGE = "message"

# Seen in the portal: "<name> heeft een lage batterij!" and "<name> heeft op de
# SOS knop gedrukt!". The English texts are assumptions; unmatched messages are
# still fired as "message", with the full text in the event data.
_LOW_BATTERY_RE = re.compile(r"lage batterij|low batter", re.I)
_SOS_RE = re.compile(r"\bSOS\b", re.I)


def classify_message(text: str) -> str:
    """Return the event type for a message text."""
    if _SOS_RE.search(text):
        return EVENT_SOS
    if _LOW_BATTERY_RE.search(text):
        return EVENT_LOW_BATTERY
    return EVENT_MESSAGE


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: One2TrackConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up One2Track event entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        One2TrackMessageEvent(coordinator, device["uuid"])
        for device in coordinator.device_list
    )


class One2TrackMessageEvent(One2TrackEntity, EventEntity):
    """Fires an event for each new message from the watch."""

    _attr_translation_key = "message"
    _attr_event_types = [EVENT_LOW_BATTERY, EVENT_SOS, EVENT_MESSAGE]

    def __init__(self, coordinator, uuid: str) -> None:
        """Initialize the event entity."""
        super().__init__(coordinator, uuid)
        self._attr_unique_id = f"{uuid}_message"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fire one event per new message, then update state as usual."""
        for msg in self.coordinator.get_new_messages(self._uuid):
            self._trigger_event(
                classify_message(msg["text"]),
                {
                    "message": msg["text"],
                    "sender": msg["sender"],
                    "sent_at": _sent_at(msg),
                    "urgent": msg.get("urgent", False),
                },
            )
            self.async_write_ha_state()
        super()._handle_coordinator_update()


def _sent_at(msg: dict[str, str]) -> str:
    """Portal date and time, in Home Assistant's time zone (minute precision)."""
    naive = datetime.strptime(f"{msg['date']} {msg['time']}", "%Y-%m-%d %H:%M")
    return naive.replace(tzinfo=dt_util.get_default_time_zone()).isoformat()
