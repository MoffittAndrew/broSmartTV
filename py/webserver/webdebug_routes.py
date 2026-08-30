"""Reverse-proxied Chrome DevTools Protocol access to the embedded QWebEngineView.

Chromium's remote-debugging-port binds to 127.0.0.1 only (Qt/Chromium's default when given a
bare port, see globals.WEBDEBUG.CDP_PORT), so nothing on the network can reach it except this
process. This module fronts it on the public webserver under /webdebug so it can be reached from
the same host/port the rest of the site uses, gated by a shared-secret token: whoever holds CDP
access can execute arbitrary JS in the loaded page, read cookies/session storage, and watch
keystrokes typed into the embedded browser (streaming service logins included), so this must
never be reachable without the token, and the token must never be exposed through the
unauthenticated /logs page (see globals.WEBDEBUG.TOKEN for where it's actually printed).
"""

import asyncio
import os
import secrets

import aiohttp
from aiohttp import web

from app_logging import get_adapter
from globals import PATH, WEB

logger = get_adapter("webdebug", "webhosting")

_COOKIE_NAME = "bro_webdebug_token"
_CLIENT_KEY = "webdebug_http_client"
_CDP_ORIGIN = f"http://127.0.0.1:{WEB.DEBUG.CDP_PORT}"


def _token_matches(candidate):
    return bool(candidate) and secrets.compare_digest(candidate, WEB.DEBUG.TOKEN)


@web.middleware
async def _auth_middleware(request, handler):
    if not request.path.startswith("/webdebug"):
        return await handler(request)

    authorized_by_cookie = _token_matches(request.cookies.get(_COOKIE_NAME))
    authorized_by_query = _token_matches(request.rel_url.query.get("token"))
    if not (authorized_by_cookie or authorized_by_query):
        raise web.HTTPForbidden(text="Missing or invalid webdebug token")

    response = await handler(request)
    if authorized_by_query and not authorized_by_cookie:
        # First-time token entry: remember it in a cookie so the devtools frontend's many
        # follow-up asset/websocket requests (which can't carry a query token themselves) pass.
        response.set_cookie(
            _COOKIE_NAME,
            WEB.DEBUG.TOKEN,
            httponly=True,
            secure=request.scheme == "https",
            samesite="Strict",
        )
    return response


def _rewrite_cdp_body(body_text, request):
    """Point CDP's self-reported URLs back through this proxy instead of the internal port."""
    proxy_host = f"{request.host}/webdebug"
    ws_scheme = "wss" if request.scheme == "https" else "ws"
    rewritten = body_text.replace(f"ws://127.0.0.1:{WEB.DEBUG.CDP_PORT}", f"{ws_scheme}://{proxy_host}")
    rewritten = rewritten.replace(f"127.0.0.1:{WEB.DEBUG.CDP_PORT}", proxy_host)
    rewritten = rewritten.replace('"/devtools/', '"/webdebug/devtools/')
    if ws_scheme == "wss":
        # inspector.html only opens a secure websocket if told via `wss=`; fed `ws=` while the
        # frontend itself was loaded over https, the browser silently blocks it as mixed content
        # - every panel stays blank forever with no visible error, since no connection ever forms.
        rewritten = rewritten.replace("?ws=", "?wss=")
    return rewritten


async def _webdebug_page(request):
    return web.FileResponse(os.path.join(PATH, "webpages", "webdebug.html"))


async def _proxy_json(request):
    tail = request.match_info.get("tail", "")
    client = request.app[_CLIENT_KEY]
    try:
        async with client.get(f"{_CDP_ORIGIN}/json{tail}") as upstream:
            body = await upstream.text()
            return web.Response(
                text=_rewrite_cdp_body(body, request),
                status=upstream.status,
                content_type="application/json",
            )
    except aiohttp.ClientError as exc:
        logger.error(f"CDP /json proxy failed: {exc}")
        raise web.HTTPBadGateway(text="Debug target unreachable") from exc


async def _proxy_devtools(request):
    tail = request.match_info.get("tail", "")
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return await _proxy_devtools_ws(request, tail)
    return await _proxy_devtools_http(request, tail)


async def _proxy_devtools_http(request, tail):
    client = request.app[_CLIENT_KEY]
    url = f"{_CDP_ORIGIN}/devtools/{tail}"
    if request.query_string:
        url += f"?{request.query_string}"
    try:
        async with client.get(url) as upstream:
            body = await upstream.read()
            content_type = upstream.headers.get("Content-Type", "application/octet-stream").split(";")[0]
            if content_type in ("text/html", "text/javascript", "application/javascript"):
                body = _rewrite_cdp_body(body.decode("utf-8", errors="replace"), request).encode("utf-8")
            return web.Response(body=body, status=upstream.status, content_type=content_type)
    except aiohttp.ClientError as exc:
        logger.error(f"CDP devtools asset proxy failed: {exc}")
        raise web.HTTPBadGateway(text="Debug target unreachable") from exc


async def _proxy_devtools_ws(request, tail):
    client = request.app[_CLIENT_KEY]
    ws_server = web.WebSocketResponse()
    await ws_server.prepare(request)

    try:
        async with client.ws_connect(f"ws://127.0.0.1:{WEB.DEBUG.CDP_PORT}/devtools/{tail}") as ws_client:

            async def pump(source, sink):
                async for msg in source:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await sink.send_str(msg.data)
                    elif msg.type == aiohttp.WSMsgType.BINARY:
                        await sink.send_bytes(msg.data)
                    else:
                        break

            tasks = [
                asyncio.create_task(pump(ws_server, ws_client)),
                asyncio.create_task(pump(ws_client, ws_server)),
            ]
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:
                    task.cancel()
    except aiohttp.ClientError as exc:
        logger.error(f"CDP websocket proxy failed: {exc}")

    if not ws_server.closed:
        await ws_server.close()
    return ws_server


async def _open_client(app):
    app[_CLIENT_KEY] = aiohttp.ClientSession()


async def _close_client(app):
    client = app.get(_CLIENT_KEY)
    if client is not None:
        await client.close()


def add_routes(app):
    app.middlewares.append(_auth_middleware)
    app.on_startup.append(_open_client)
    app.on_cleanup.append(_close_client)
    app.router.add_get("/webdebug", _webdebug_page)
    app.router.add_get("/webdebug/json{tail:.*}", _proxy_json)
    app.router.add_get("/webdebug/devtools/{tail:.*}", _proxy_devtools)
