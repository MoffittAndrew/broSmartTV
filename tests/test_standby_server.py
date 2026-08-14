import asyncio
import sys
from pathlib import Path

import pytest
from aiohttp.test_utils import make_mocked_request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import standby_server


@pytest.mark.asyncio
async def test_power_status_reports_off():
    request = make_mocked_request("GET", "/power-status")

    response = await standby_server.power_status(request)

    assert response.status == 200
    assert response.body == b'{"on": false}'


@pytest.mark.asyncio
async def test_power_on_sets_wake_event():
    wake_event = asyncio.Event()
    power_on = standby_server._make_power_on(wake_event)
    request = make_mocked_request("POST", "/power-on")

    response = await power_on(request)

    assert response.status == 200
    assert wake_event.is_set()
