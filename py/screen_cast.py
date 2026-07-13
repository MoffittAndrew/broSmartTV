# this code was written by AI (I gave up)
# Launches the screen cast (via RTC) webserver and forwards video frames to the Qt UI

print("Importing screen cast server...")

import os
import asyncio
import json
import ssl
import time
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


def _pc_tag(pc):
    return f"pc-{id(pc):x}"


async def _cleanup_peer(pc):
    global active_pc

    tag = _pc_tag(pc)

    if pc in pcs:
        pcs.discard(pc)

    if active_pc == pc:
        active_pc = None

    try:
        await pc.close()
        print(f"[{tag}] Peer connection closed.")
    except Exception as exc:
        print(f"[{tag}] Peer cleanup close failed: {exc}")


async def index(request):
    return web.FileResponse(os.path.join(PATH, "web", "index.html"))


async def offer(request):
    global active_pc

    if active_pc is not None and active_pc.connectionState not in ("closed", "failed"):
        print(f"Rejecting new connection: stream busy (active={_pc_tag(active_pc)}, state={active_pc.connectionState})")
        return web.Response(
            status=403,
            text="Stream busy — another client is currently connected."
        )

    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)
    active_pc = pc
    tag = _pc_tag(pc)
    print(f"[{tag}] New PeerConnection created (remote={request.remote})")

    @pc.on("track")
    def on_track(track):
        print(f"[{tag}] Track received: {track.kind}")

        if track.kind == "video":
            _notifyConnected()
            print(f"[{tag}] Showing screen-cast view while waiting for frames.")

            async def read_frames():
                frame_timeout = SCREEN_CAST.FRAME_TIMEOUT_SECONDS
                log_interval = SCREEN_CAST.FRAME_LOG_INTERVAL_SECONDS
                start_time = time.monotonic()
                last_frame_time = None
                last_log_time = start_time
                frame_count = 0

                try:
                    while True:
                        try:
                            frame = await asyncio.wait_for(track.recv(), timeout=frame_timeout)
                        except asyncio.TimeoutError:
                            if frame_count == 0:
                                print(f"[{tag}] No video frames received within {frame_timeout}s; terminating stalled stream.")
                            else:
                                stalled_for = time.monotonic() - (last_frame_time or start_time)
                                print(
                                    f"[{tag}] Frame receive stalled for {stalled_for:.1f}s "
                                    f"(timeout={frame_timeout}s, total_frames={frame_count}); terminating stream."
                                )
                            break

                        now = time.monotonic()
                        frame_count += 1
                        last_frame_time = now

                        if frame_count == 1:
                            print(f"[{tag}] First video frame received after {now - start_time:.2f}s.")

                        if now - last_log_time >= log_interval:
                            elapsed = max(now - start_time, 1e-6)
                            avg_fps = frame_count / elapsed
                            print(
                                f"[{tag}] Frame stats: frames={frame_count}, elapsed={elapsed:.1f}s, "
                                f"avg_fps={avg_fps:.1f}."
                            )
                            last_log_time = now

                        frame_array = frame.to_ndarray(format="rgb24")

                        _notifyFrame(frame_array)
                except Exception as exc:
                    print(f"[{tag}] Stream ended with error: {exc}")
                finally:
                    total_elapsed = time.monotonic() - start_time
                    print(
                        f"[{tag}] Stream reader stopping (frames={frame_count}, elapsed={total_elapsed:.1f}s, "
                        f"connectionState={pc.connectionState})."
                    )
                    await _cleanup_peer(pc)
                    _notifyDisconnected()

            task = asyncio.create_task(read_frames())
            _track_tasks.add(task)
            task.add_done_callback(_track_tasks.discard)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"[{tag}] Connection state changed: {pc.connectionState}")
        if pc.connectionState in ("failed", "closed", "disconnected"):
            await _cleanup_peer(pc)
            _notifyDisconnected()

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print(f"[{tag}] ICE connection state changed: {pc.iceConnectionState}")

    @pc.on("signalingstatechange")
    def on_signalingstatechange():
        print(f"[{tag}] Signaling state changed: {pc.signalingState}")

    await pc.setRemoteDescription(offer)
    print(f"[{tag}] Remote description set (type={offer.type}).")
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    print(f"[{tag}] Local description created (type={pc.localDescription.type}).")

    return web.Response(
        content_type="application/json",
        text=json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }),
    )


async def on_shutdown(screenCastServer):
    print(f"Server shutting down, closing peer connections... (count={len(pcs)})")
    coros = [_cleanup_peer(pc) for pc in list(pcs)]
    await asyncio.gather(*coros)
    pcs.clear()
    global active_pc
    active_pc = None
    _notifyDisconnected()


async def status(request):
    busy = active_pc is not None and active_pc.connectionState not in ("closed", "failed")
    return web.json_response({"available": not busy})


async def capture_settings(request):
    return web.json_response({
        "width": SCREEN_CAST.CAPTURE_WIDTH,
        "height": SCREEN_CAST.CAPTURE_HEIGHT,
        "frameRate": SCREEN_CAST.CAPTURE_FRAME_RATE,
    })


screenCastServer = web.Application()
screenCastServer.on_shutdown.append(on_shutdown)
screenCastServer.router.add_get("/", index)
screenCastServer.router.add_post("/offer", offer)
screenCastServer.router.add_get("/status", status)
screenCastServer.router.add_get("/capture-settings", capture_settings)


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