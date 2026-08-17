import sys
from pathlib import Path

import pytest
from aiohttp.test_utils import make_mocked_request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import webserver.screen_cast as screen_cast
import webserver.standby_server as standby_server


@pytest.mark.asyncio
async def test_screen_cast_root_redirects_to_cast_page():
    request = make_mocked_request("GET", "/")

    response = await screen_cast.index(request)

    assert response.status == 302
    assert response.headers["Location"] == "/cast"


@pytest.mark.asyncio
async def test_standby_server_redirects_main_pages_to_standby():
    request = make_mocked_request("GET", "/cast")

    response = await standby_server.redirect_to_standby("/cast")(request)

    assert response.status == 302
    assert response.headers["Location"] == "/standby?next=/cast"
