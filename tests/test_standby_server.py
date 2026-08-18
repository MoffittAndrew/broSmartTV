import asyncio
import sys
from pathlib import Path

import pytest
from aiohttp.test_utils import make_mocked_request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import webserver.standby_server as standby_server


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


@pytest.mark.asyncio
async def test_future_standby_page_redirects_with_destination():
    request = make_mocked_request("GET", "/future")

    response = await standby_server.future_page(request)

    assert response.status == 302
    assert response.headers["Location"] == "/standby?next=/future"


@pytest.mark.asyncio
async def test_logs_route_remains_available_while_standby():
    app = standby_server._build_app(asyncio.Event())
    request = make_mocked_request("GET", "/logs")

    match = await app.router.resolve(request)

    assert match.handler.__name__ == "logs_page"
