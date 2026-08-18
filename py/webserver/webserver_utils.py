"""Shared aiohttp runner/site start-stop helpers.

Kept dependency-light (only aiohttp/ssl/errno) so modules that need to host a
webpage without pulling in the heavy aiortc/audio_playback stack (e.g. the
standby server) can reuse the same runner/SSL/error-handling logic as the
full screen cast server.
"""

import errno
import os
import ssl

from aiohttp import web

from app_logging import get_adapter
from globals import SCREEN_CAST


def build_static_file_handler(static_root):
    """Return an aiohttp handler serving files under static_root, rejecting traversal outside it."""
    static_root = os.path.realpath(static_root)

    async def serve_static_file(request):
        filename = request.match_info.get("filename", "")
        if not filename:
            raise web.HTTPNotFound()

        safe_path = os.path.normpath(filename).lstrip("/\\")
        if not safe_path or safe_path == "." or safe_path.startswith(".."):
            raise web.HTTPForbidden()

        target = os.path.realpath(os.path.join(static_root, safe_path))
        if os.path.commonpath([static_root, target]) != static_root or not os.path.isfile(target):
            raise web.HTTPNotFound()

        return web.FileResponse(target)

    return serve_static_file


async def start_site(application, host, port, log_prefix):
    logger = get_adapter("webserver", log_prefix)
    runner = web.AppRunner(application)
    await runner.setup()

    ssl_context = None
    scheme = "http"
    if SCREEN_CAST.SSL_CERT and SCREEN_CAST.SSL_KEY:
        try:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(SCREEN_CAST.SSL_CERT, SCREEN_CAST.SSL_KEY)
            scheme = "https"
        except Exception as exc:
            logger.error(f"Failed to enable HTTPS: {exc}")
            logger.warning("Falling back to HTTP.")
            ssl_context = None

    site = web.TCPSite(runner, host, port, ssl_context=ssl_context)
    try:
        await site.start()
    except OSError as exc:
        await runner.cleanup()
        if exc.errno == errno.EACCES:
            raise RuntimeError(
                f"Server cannot bind {host}:{port}: permission denied. "
                "For ports below 1024, grant the runtime Python executable "
                "CAP_NET_BIND_SERVICE."
            ) from exc
        raise RuntimeError(f"Server could not bind {host}:{port}: {exc}") from exc

    if SCREEN_CAST.IP is not None:
        logger.info(f"Started at {scheme}://{SCREEN_CAST.IP}:{port}")
    else:
        logger.info(f"Started on port {port} (LAN IP unavailable, scheme={scheme})")

    return runner, site


async def stop_site(runner, site):
    if site is not None:
        await site.stop()

    if runner is not None:
        await runner.cleanup()
