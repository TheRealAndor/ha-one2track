"""Tests for parsing One2Track portal pages (anonymised fixtures)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.one2track.api import One2TrackApiClient

DEVICE_PAGE = """
<div class='row'>
<div class='col-sm-4'><img src="/avatar.png" /></div>
<div class='col-sm-8'>
<h4>
Sam
</h4>
<span>
<img style="width: 12px; height: 12px;" src="/assets/device_location_gps.png" />
<span>
0000000000
</span>
</span>
<br>
MODEL
<br>
<br>
<span>
0031600000000
</span>
</div>
</div>
<script>
var device = {"uuid": "abc", "name": "Sam", "device_model_id": 377};
var last_location = {"latitude": "52.0", "longitude": "5.0", "meta_data": {"steps": 10}};
</script>
"""


@pytest.fixture
def client() -> One2TrackApiClient:
    """Return an API client that never touches the network."""
    return One2TrackApiClient(username="sam", password="secret", session=MagicMock())


@pytest.mark.parametrize("model", ["Connect MOVE", "Connect NEXT", "Connect YOU"])
def test_device_page_model_name(client: One2TrackApiClient, model: str) -> None:
    """The model name shown on the watch card is read from the device page."""
    result = client._parse_device_page(DEVICE_PAGE.replace("MODEL", model), "abc")
    assert result["model_name"] == model
    assert result["device"]["device_model_id"] == 377
    assert result["last_location"]["meta_data"] == {"steps": 10}


def test_device_page_without_model_name(client: One2TrackApiClient) -> None:
    """A page without the watch card gives no model name, but still the data."""
    html = '<script>var device = {"uuid": "abc", "device_model_id": 189};</script>'
    result = client._parse_device_page(html, "abc")
    assert "model_name" not in result
    assert result["device"]["device_model_id"] == 189
