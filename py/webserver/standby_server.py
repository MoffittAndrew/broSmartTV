"""Lightweight "TV is off" webserver.

Hosted from launch.py before init_qt()/QApplication exist, so the box stays
low memory/power while waiting for a wake trigger (remote found or someone
hitting the web "turn bro on" button). Deliberately avoids importing
screen_cast.py (which pulls in aiortc/audio_playback) - this module only
needs aiohttp.
"""

print("Importing standby server...")

import os

from aiohttp import web

from globals import PATH, SCREEN_CAST
from webserver.webserver_utils import start_site, stop_site, build_static_file_handler

LOG_PREFIX = "[standby]"


def log(message):
    print(f"{LOG_PREFIX} {message}")


async def index(request):
    return web.FileResponse(os.path.join(PATH, "web", "index.html"))


async def cast(request):
    return web.FileResponse(os.path.join(PATH, "web", "standby.html"))


serve_static_file = build_static_file_handler(os.path.join(PATH, "web"))


async def power_status(request):
    # Reachable only while the TV is off; the full server takes over /power-status once on.
    return web.json_response({"on": False})


def _make_power_on(wake_event):
    async def power_on(request):
        wake_event.set()
        return web.json_response({"ok": True})

    return power_on


def _build_app(wake_event):
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/cast", cast)
    # /remote is aliased to the same "turn bro on" page while off; the full server takes over with the real remote UI once awake.
    app.router.add_get("/remote", cast)
    app.router.add_get("/{filename:.*\\.(js|css|html|json|map|svg|png|jpg|jpeg|gif|webp)}", serve_static_file)
    app.router.add_get("/power-status", power_status)
    app.router.add_post("/power-on", _make_power_on(wake_event))
    return app


_runner = None
_site = None


async def start_standby_server(wake_event, host=SCREEN_CAST.HOST, port=SCREEN_CAST.PORT):
    global _runner, _site

    if _runner is not None:
        return

    _runner, _site = await start_site(_build_app(wake_event), host, port, LOG_PREFIX)


async def stop_standby_server():
    global _runner, _site

    await stop_site(_runner, _site)
    _runner = None
    _site = None
