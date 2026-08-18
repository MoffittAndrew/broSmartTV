"""Lightweight "TV is off" webserver.

Hosted from launch.py before init_qt()/QApplication exist, so the box stays
low memory/power while waiting for a wake trigger (remote found or someone
hitting the web "turn bro on" button). Deliberately avoids importing
screen_cast.py (which pulls in aiortc/audio_playback) - this module only
needs aiohttp.
"""

from app_logging import get_adapter

logger = get_adapter("standby", "standby")
logger.info("Importing standby server...")

import os
from urllib.parse import quote

from aiohttp import web

from globals import PATH, SCREEN_CAST
from webserver.logs_routes import add_routes as add_logs_routes
from webserver.webserver_utils import start_site, stop_site, build_static_file_handler

WEBPAGES_DIR = os.path.join(PATH, "webpages")


def log(message, level="INFO", **fields):
    return logger.log(level, message, **fields)


def _normalize_next_path(next_path):
    if isinstance(next_path, str) and next_path.startswith("/"):
        return next_path
    return "/cast"


def redirect_to_standby(next_path):
    target = _normalize_next_path(next_path)

    async def redirect(request):
        return web.HTTPFound(f"/standby?next={quote(target, safe='')}")

    return redirect


async def index(request):
    return web.HTTPFound("/cast")


async def cast(request):
    return await redirect_to_standby("/cast")(request)


async def remote(request):
    return web.FileResponse(os.path.join(WEBPAGES_DIR, "remote.html"))


async def future_page(request):
    return await redirect_to_standby(request.path)(request)


async def standby_page(request):
    return web.FileResponse(os.path.join(WEBPAGES_DIR, "standby.html"))


serve_static_file = build_static_file_handler(WEBPAGES_DIR)


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
    app.router.add_get("/remote", remote)
    app.router.add_get("/standby", standby_page)
    add_logs_routes(app)
    app.router.add_get("/{filename:.*\\.(js|css|html|json|map|svg|png|jpg|jpeg|gif|webp)}", serve_static_file)
    app.router.add_get("/power-status", power_status)
    app.router.add_post("/power-on", _make_power_on(wake_event))
    app.router.add_get("/{page:[^/]+}", future_page)
    return app


_runner = None
_site = None


async def start_standby_server(wake_event, host=SCREEN_CAST.HOST, port=SCREEN_CAST.PORT):
    global _runner, _site

    if _runner is not None:
        return

    _runner, _site = await start_site(_build_app(wake_event), host, port, "standby")


async def stop_standby_server():
    global _runner, _site

    await stop_site(_runner, _site)
    _runner = None
    _site = None
