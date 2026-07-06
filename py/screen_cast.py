# this code was written by AI (I gave up)
# Launches the screen cast (via RTC) webserver and forwards video frames to the Qt UI

print("Importing screen cast server...")

import os
import asyncio
import json
import ssl
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from globals import PATH, SCREEN_CAST

pcs = set()
active_pc = None  # only one active peer connection at a time
_track_tasks = set()

_frame_handler = None
_connection_handler = None
_disconnect_handler = None


def setFrameHandler(callback):
    global _frame_handler
    _frame_handler = callback


def setConnectionHandler(callback):
    global _connection_handler
    _connection_handler = callback


def setDisconnectHandler(callback):
    global _disconnect_handler
    _disconnect_handler = callback


def _notifyFrame(frame):
    if _frame_handler is not None:
        _frame_handler(frame)


def _notifyConnected():
    if _connection_handler is not None:
        _connection_handler()


def _notifyDisconnected():
    if _disconnect_handler is not None:
        _disconnect_handler()


async def _cleanup_peer(pc):
    global active_pc

    if pc in pcs:
        pcs.discard(pc)

    if active_pc == pc:
        active_pc = None

    try:
        await pc.close()
    except Exception:
        pass


async def index(request):
    return web.FileResponse(os.path.join(PATH, "web", "index.html"))


async def offer(request):
    global active_pc

    if active_pc is not None and active_pc.connectionState not in ("closed", "failed"):
        print("Rejecting new connection: stream busy")
        return web.Response(
            status=403,
            text="Stream busy — another client is currently connected."
        )

    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)
    active_pc = pc
    print("New PeerConnection created")

    @pc.on("track")
    def on_track(track):
        print(f"Track received: {track.kind}")

        if track.kind == "video":
            _notifyConnected()

            async def read_frames():
                try:
                    while True:
                        frame = await track.recv()
                        frame_array = frame.to_ndarray(format="bgr24")

                        _notifyFrame(frame_array)
                except Exception as exc:
                    print("Stream ended:", exc)
                finally:
                    await _cleanup_peer(pc)
                    _notifyDisconnected()

            task = asyncio.create_task(read_frames())
            _track_tasks.add(task)
            task.add_done_callback(_track_tasks.discard)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state changed: {pc.connectionState}")
        if pc.connectionState in ("failed", "closed", "disconnected"):
            await _cleanup_peer(pc)
            _notifyDisconnected()

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }),
    )


async def on_shutdown(screenCastServer):
    print("Server shutting down, closing peer connections...")
    coros = [_cleanup_peer(pc) for pc in list(pcs)]
    await asyncio.gather(*coros)
    pcs.clear()
    global active_pc
    active_pc = None
    _notifyDisconnected()


async def status(request):
    busy = active_pc is not None and active_pc.connectionState not in ("closed", "failed")
    return web.json_response({"available": not busy})


screenCastServer = web.Application()
screenCastServer.on_shutdown.append(on_shutdown)
screenCastServer.router.add_get("/", index)
screenCastServer.router.add_post("/offer", offer)
screenCastServer.router.add_get("/status", status)


_runner = None
_site = None

async def startScreenCastServer(host=SCREEN_CAST.HOST, port=SCREEN_CAST.PORT):
    global _runner, _site

    if _runner is not None:
        return

    _runner = web.AppRunner(screenCastServer)
    await _runner.setup()

    ssl_context = None
    scheme = "http"
    if SCREEN_CAST.SSL_CERT and SCREEN_CAST.SSL_KEY:
        try:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(SCREEN_CAST.SSL_CERT, SCREEN_CAST.SSL_KEY)
            scheme = "https"
        except Exception as exc:
            print(f"Failed to enable HTTPS for screen cast server: {exc}")
            print("Falling back to HTTP.")
            ssl_context = None

    _site = web.TCPSite(_runner, host, port, ssl_context=ssl_context)
    await _site.start()
    if SCREEN_CAST.IP is not None:
        print(f"Screen cast server started at {scheme}://{SCREEN_CAST.IP}:{port}")
    else:
        print(f"Screen cast server started on port {port} (LAN IP unavailable, scheme={scheme})")

async def stopScreenCastServer():
    global _runner, _site

    if _site is not None:
        await _site.stop()
        _site = None

    if _runner is not None:
        await _runner.cleanup()
        _runner = None