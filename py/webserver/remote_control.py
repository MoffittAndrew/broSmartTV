"""Virtual remote webpage: serves remote.html and forwards button events into InputInterface.

Only registered on the full screen_cast server (see screen_cast.py) - during
standby, /remote is aliased to the standby "turn bro on" page instead (see
standby_server.py), since there is no InputInterface to receive events yet.
"""

import os

from aiohttp import web

from globals import PATH, INPUT

LOG_PREFIX = "[remote]"

# Whitelist of valid button names, built from globals.INPUT so an arbitrary
# string can't be injected into the InputInterface backlog via the request body.
_ALLOWED_BUTTONS = {
    INPUT.POWER,
    INPUT.HOME,
    INPUT.SELECT,
    INPUT.NAV_UP,
    INPUT.NAV_RIGHT,
    INPUT.NAV_DOWN,
    INPUT.NAV_LEFT,
    INPUT.MENU,
    INPUT.RETURN,
    INPUT.VOL_UP,
    INPUT.VOL_DOWN,
    INPUT.MIC,
}
_ALLOWED_STATES = {"press", "release"}


def log(message):
    print(f"{LOG_PREFIX} {message}")


async def remote_page(request):
    return web.FileResponse(os.path.join(PATH, "web", "remote.html"))


async def handle_input(request):
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON body"}, status=400)

    button = payload.get("button")
    state = payload.get("state")

    if button not in _ALLOWED_BUTTONS or state not in _ALLOWED_STATES:
        return web.json_response({"error": "invalid button or state"}, status=400)

    wire_value = button if state == "press" else INPUT.RELEASED_PREFIX + button

    # Imported lazily to avoid a teardown -> screen_cast -> remote_control -> input_interface -> teardown import cycle.
    from interface.input_interface import inputInterface

    inputInterface.receive(wire_value)
    return web.json_response({"ok": True})


def add_routes(app):
    app.router.add_get("/remote", remote_page)
    app.router.add_post("/input", handle_input)
