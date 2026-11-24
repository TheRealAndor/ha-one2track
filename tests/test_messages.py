"""Tests for reading portal messages and turning new ones into events."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.one2track.api import (
    One2TrackApiClient,
    One2TrackApiClientCommunicationError,
)
from custom_components.one2track.coordinator import One2TrackCoordinator
from custom_components.one2track.event import classify_message

UUID = "watch-1"
MESSAGES_HTML = (Path(__file__).parent / "fixtures" / "messages.html").read_text(
    encoding="utf-8"
)


def _msg(
    date: str, time: str, text: str, direction: str = "ltr", sender: str = "Sam"
) -> dict:
    return {
        "date": date,
        "time": time,
        "sender": sender,
        "text": text,
        "direction": direction,
        "urgent": False,
    }


# ── Parser ────────────────────────────────────────────────────────────


def test_parse_messages() -> None:
    """Every block is read in page order, with the date of the badge above it."""
    messages = One2TrackApiClient._parse_messages(MESSAGES_HTML)
    assert messages == [
        {
            "date": "2026-09-17",
            "time": "09:32",
            "sender": "Sam",
            "text": "Sam heeft een lage batterij!",
            "direction": "ltr",
            "urgent": False,
        },
        {
            "date": "2026-11-18",
            "time": "18:46",
            "sender": "Alex Parent",
            "text": "Hallo & tot zo",
            "direction": "rtl",
            "urgent": False,
        },
        {
            "date": "2026-11-18",
            "time": "18:46",
            "sender": "Sam",
            "text": "Sam heeft op de SOS knop gedrukt!",
            "direction": "ltr",
            "urgent": True,
        },
    ]


def test_parse_messages_sent_message_does_not_swallow_sos() -> None:
    """A portal message ("Verstuurd" after the time) followed by an SOS gives both.

    This combination once made the SOS disappear into the block before it.
    """
    messages = One2TrackApiClient._parse_messages(MESSAGES_HTML)
    assert [m["direction"] for m in messages[-2:]] == ["rtl", "ltr"]
    assert messages[-1]["urgent"] is True


def test_parse_messages_empty_page() -> None:
    """A watch without messages gives an empty list."""
    assert One2TrackApiClient._parse_messages("<div id='messages-container'></div>") == []


def test_parse_messages_skips_block_without_date() -> None:
    """A block before any date badge cannot be dated and is skipped."""
    html = MESSAGES_HTML[MESSAGES_HTML.index("<div class='col-12'>") :]
    first = html.index("m-badge--wide")
    assert One2TrackApiClient._parse_messages(html[:first]) == []


# ── Classification ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("text", "event_type"),
    [
        ("Sam heeft op de SOS knop gedrukt!", "sos"),
        ("Sam pressed the SOS button!", "sos"),
        ("Sam heeft een lage batterij!", "low_battery"),
        ("Sam has a low battery!", "low_battery"),
        ("Ik ben bij opa", "message"),
        ("Sossen is lekker", "message"),
    ],
)
def test_classify_message(text: str, event_type: str) -> None:
    """SOS and low battery alerts get their own event type; the rest is a message."""
    assert classify_message(text) == event_type


# ── Detection of new messages ────────────────────────────────────────


@pytest.fixture
def coordinator(hass: HomeAssistant) -> One2TrackCoordinator:
    """A coordinator with a fake client and without writing to storage."""
    client = MagicMock()
    client.async_get_messages = AsyncMock(return_value=[])
    return One2TrackCoordinator(hass, client, None)


@pytest.fixture(autouse=True)
def no_save() -> Generator[None]:
    """Do not write the message marks to storage."""
    with patch.object(One2TrackCoordinator, "_async_save_settings", AsyncMock()):
        yield


async def _fetch(coordinator: One2TrackCoordinator, messages: list[dict]) -> list[dict]:
    coordinator.client.async_get_messages.return_value = messages
    return await coordinator._async_fetch_new_messages(UUID)


async def test_first_run_only_marks_existing_messages(
    coordinator: One2TrackCoordinator,
) -> None:
    """Installing the integration does not replay old alerts."""
    old = [_msg("2026-11-18", "18:46", "Sam heeft op de SOS knop gedrukt!")]
    assert await _fetch(coordinator, old) == []
    assert await _fetch(coordinator, old) == []


async def test_new_message_is_reported_once(coordinator: One2TrackCoordinator) -> None:
    """A message after the last seen one is reported, and only once."""
    old = [_msg("2026-11-18", "18:46", "Hoi")]
    await _fetch(coordinator, old)
    sos = _msg("2026-11-19", "07:15", "Sam heeft op de SOS knop gedrukt!")
    assert await _fetch(coordinator, [*old, sos]) == [sos]
    assert await _fetch(coordinator, [*old, sos]) == []


async def test_new_message_in_same_minute(coordinator: One2TrackCoordinator) -> None:
    """A different message in the same minute as the last seen one is still new."""
    first = _msg("2026-11-18", "18:46", "Hoi")
    await _fetch(coordinator, [first])
    second = _msg("2026-11-18", "18:46", "Sam heeft op de SOS knop gedrukt!")
    assert await _fetch(coordinator, [first, second]) == [second]
    assert await _fetch(coordinator, [first, second]) == []


async def test_portal_messages_are_ignored(coordinator: One2TrackCoordinator) -> None:
    """Messages sent from the portal (rtl) are not reported as events."""
    await _fetch(coordinator, [])
    sent = _msg("2026-11-18", "18:46", "Kom je eten?", direction="rtl", sender="Alex")
    assert await _fetch(coordinator, [sent]) == []


async def test_first_message_ever(coordinator: One2TrackCoordinator) -> None:
    """A watch without messages reports its very first message."""
    assert await _fetch(coordinator, []) == []
    first = _msg("2026-11-19", "08:00", "Hoi")
    assert await _fetch(coordinator, [first]) == [first]


async def test_restart_keeps_seen_messages(
    hass: HomeAssistant, coordinator: One2TrackCoordinator
) -> None:
    """After a restart the stored mark prevents old messages from firing again."""
    old = [_msg("2026-11-18", "18:46", "Hoi")]
    await _fetch(coordinator, old)
    restarted = One2TrackCoordinator(hass, coordinator.client, None)
    restarted._message_marks = dict(coordinator._message_marks)
    assert await _fetch(restarted, old) == []


async def test_portal_error_gives_no_messages(
    coordinator: One2TrackCoordinator,
) -> None:
    """A failing messages page does not break the update."""
    await _fetch(coordinator, [])
    coordinator.client.async_get_messages.side_effect = (
        One2TrackApiClientCommunicationError("down")
    )
    assert await coordinator._async_fetch_new_messages(UUID) == []
