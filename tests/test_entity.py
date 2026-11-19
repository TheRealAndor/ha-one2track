"""Tests for the device information of a watch."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.one2track.entity import One2TrackEntity


@pytest.mark.parametrize(
    ("data", "model"),
    [
        ({"model_name": "Connect YOU", "device_model_id": 999}, "Connect YOU"),
        ({"device_model_id": 189}, "Connect NEXT"),
        ({"device_model_id": 377}, "Connect YOU"),
        ({"device_model_id": 27}, "Connect MOVE"),
        ({"device_model_id": 999}, "Unknown (999)"),
        ({}, None),
    ],
)
def test_model_name(data: dict, model: str | None) -> None:
    """The portal's model name wins; otherwise the known name for the model ID."""
    coordinator = MagicMock()
    coordinator.get_device_data.return_value = {"name": "Sam", **data}
    entity = One2TrackEntity(coordinator, "abc")
    info = entity.device_info
    assert info["model"] == model
    expected_id = str(data["device_model_id"]) if "device_model_id" in data else None
    assert info.get("model_id") == expected_id
