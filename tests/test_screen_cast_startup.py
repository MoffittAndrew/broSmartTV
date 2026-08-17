import errno
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

import web_server.screen_cast as screen_cast
import web_server.web_server_utils as web_server_utils


class FakeRunner:
    def __init__(self, _application):
        self.setup_called = False
        self.cleanup_called = False

    async def setup(self):
        self.setup_called = True

    async def cleanup(self):
        self.cleanup_called = True


@pytest.mark.asyncio
async def test_start_screen_cast_server_records_started_resources(monkeypatch):
    created_runners = []
    created_sites = []

    class FakeSite:
        def __init__(self, runner, host, port, ssl_context=None):
            self.runner = runner
            self.host = host
            self.port = port
            self.ssl_context = ssl_context
            self.started = False

        async def start(self):
            self.started = True

    def create_runner(application):
        runner = FakeRunner(application)
        created_runners.append(runner)
        return runner

    def create_site(*args, **kwargs):
        site = FakeSite(*args, **kwargs)
        created_sites.append(site)
        return site

    monkeypatch.setattr(web_server_utils.web, "AppRunner", create_runner)
    monkeypatch.setattr(web_server_utils.web, "TCPSite", create_site)
    monkeypatch.setattr(web_server_utils.SCREEN_CAST, "SSL_CERT", None)
    monkeypatch.setattr(web_server_utils.SCREEN_CAST, "SSL_KEY", None)
    monkeypatch.setattr(web_server_utils.SCREEN_CAST, "IP", None)
    monkeypatch.setattr(screen_cast, "_runner", None)
    monkeypatch.setattr(screen_cast, "_site", None)

    await screen_cast.startScreenCastServer(host="127.0.0.1", port=8443)

    assert created_runners[0].setup_called is True
    assert created_sites[0].started is True
    assert screen_cast._runner is created_runners[0]
    assert screen_cast._site is created_sites[0]


@pytest.mark.asyncio
async def test_start_screen_cast_server_cleans_up_permission_denied(monkeypatch):
    created_runners = []

    class DeniedSite:
        def __init__(self, *_args, **_kwargs):
            pass

        async def start(self):
            raise PermissionError(errno.EACCES, "Permission denied")

    def create_runner(application):
        runner = FakeRunner(application)
        created_runners.append(runner)
        return runner

    monkeypatch.setattr(web_server_utils.web, "AppRunner", create_runner)
    monkeypatch.setattr(web_server_utils.web, "TCPSite", DeniedSite)
    monkeypatch.setattr(web_server_utils.SCREEN_CAST, "SSL_CERT", None)
    monkeypatch.setattr(web_server_utils.SCREEN_CAST, "SSL_KEY", None)
    monkeypatch.setattr(screen_cast, "_runner", None)
    monkeypatch.setattr(screen_cast, "_site", None)

    with pytest.raises(RuntimeError, match="CAP_NET_BIND_SERVICE"):
        await screen_cast.startScreenCastServer(host="0.0.0.0", port=443)

    assert created_runners[0].setup_called is True
    assert created_runners[0].cleanup_called is True
    assert screen_cast._runner is None
    assert screen_cast._site is None