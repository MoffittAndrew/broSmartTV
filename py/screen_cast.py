# this code was written by AI (I gave up)
# Launches the screen cast (via RTC) webserver and forwards video frames to the Qt UI

print("Importing screen cast server...")

import os
import asyncio
import json
import time
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from globals import PATH, SCREEN_CAST
from audio_playback import submitAudioFrame, stopAudioPlayback
from web_server_utils import start_site, stop_site, build_static_file_handler

LOG_PREFIX = "[screencast]"

pcs = set()
active_pc = None  # only one active peer connection at a time
_track_tasks = set()
_cleaning_peers = set()

_frame_handler = None
_connection_handler = None
_disconnect_handler = None


def log(message):
    print(f"{LOG_PREFIX} {message}")


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


def _count_sdp_candidates(sdp):
    if not sdp:
        return 0
    return sum(1 for line in sdp.splitlines() if line.startswith("a=candidate:"))


def _rtc_configuration():
    return RTCConfiguration(
        iceServers=[RTCIceServer(urls=url) for url in SCREEN_CAST.ICE_SERVERS]
    )


async def _wait_for_ice_gathering_complete(pc, timeout_seconds):
    start = time.monotonic()
    while pc.iceGatheringState != "complete":
        if time.monotonic() - start >= timeout_seconds:
            log(
                f"ICE gathering wait timed out after {timeout_seconds}s "
                f"(state={pc.iceGatheringState}); proceeding with current candidates."
            )
            return False
        await asyncio.sleep(0.05)

    elapsed = time.monotonic() - start
    log(f"ICE gathering complete after {elapsed:.2f}s.")
    return True


async def _cleanup_peer(pc):
    global active_pc

    if pc in _cleaning_peers:
        return

    _cleaning_peers.add(pc)

    try:
        if pc in pcs:
            pcs.discard(pc)

        if active_pc == pc:
            active_pc = None

        try:
            await stopAudioPlayback()
        except Exception as exc:
            log(f"Audio playback cleanup failed: {exc}")

        try:
            await pc.close()
            log("Peer connection closed.")
        except Exception as exc:
            log(f"Peer cleanup close failed: {exc}")
    finally:
        _cleaning_peers.discard(pc)


async def index(request):
    return web.FileResponse(os.path.join(PATH, "web", "index.html"))


async def cast(request):
    return web.FileResponse(os.path.join(PATH, "web", "cast.html"))


serve_static_file = build_static_file_handler(os.path.join(PATH, "web"))


async def offer(request):
    global active_pc

    if active_pc is not None and active_pc.connectionState not in ("closed", "failed"):
        log(f"Rejecting new connection: stream busy (state={active_pc.connectionState})")
        return web.Response(
            status=403,
            text="Stream busy — another client is currently connected."
        )

    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    offer_candidates = _count_sdp_candidates(offer.sdp)

    pc = RTCPeerConnection(configuration=_rtc_configuration())
    pcs.add(pc)
    active_pc = pc
    log(f"New peer connection created (remote={request.remote})")
    log(f"Offer metadata: type={offer.type}, candidate_count={offer_candidates}.")

    @pc.on("track")
    def on_track(track):
        log(f"Track received: {track.kind}")

        if track.kind == "video":
            _notifyConnected()
            log("Showing screen-cast view while waiting for frames.")

            async def read_frames():
                frame_timeout = SCREEN_CAST.FRAME_TIMEOUT_SECONDS
                log_interval = SCREEN_CAST.FRAME_LOG_INTERVAL_SECONDS
                receiver_drain_timeout = SCREEN_CAST.RECEIVER_DRAIN_TIMEOUT_SECONDS
                start_time = time.monotonic()
                last_frame_time = None
                last_log_time = start_time
                frame_count = 0
                coalesced_before_ui = 0

                try:
                    while True:
                        try:
                            frame = await asyncio.wait_for(track.recv(), timeout=frame_timeout)
                        except asyncio.TimeoutError:
                            if frame_count == 0:
                                log(f"No video frames received within {frame_timeout}s; terminating stalled stream.")
                            else:
                                stalled_for = time.monotonic() - (last_frame_time or start_time)
                                log(
                                    f"Frame receive stalled for {stalled_for:.1f}s "
                                    f"(timeout={frame_timeout}s, total_frames={frame_count}); terminating stream."
                                )
                            break

                        now = time.monotonic()
                        frame_count += 1
                        last_frame_time = now

                        # Drain any immediately available decoded backlog so we
                        # forward only the freshest frame. This avoids the
                        # visible lag-then-fast-forward behavior under pressure.
                        while True:
                            try:
                                frame = await asyncio.wait_for(track.recv(), timeout=receiver_drain_timeout)
                                coalesced_before_ui += 1
                                frame_count += 1
                                last_frame_time = time.monotonic()
                            except asyncio.TimeoutError:
                                break

                        if frame_count == 1:
                            log(f"First video frame received after {now - start_time:.2f}s.")

                        if now - last_log_time >= log_interval:
                            elapsed = max(now - start_time, 1e-6)
                            avg_fps = frame_count / elapsed
                            log(
                                f"Frame stats: frames={frame_count}, elapsed={elapsed:.1f}s, "
                                f"avg_fps={avg_fps:.1f}, coalesced_before_ui={coalesced_before_ui}."
                            )
                            last_log_time = now

                        # Send raw frames to the UI callback so receiver-side
                        # coalescing can drop stale frames before expensive
                        # RGB numpy conversion is performed.
                        _notifyFrame(frame)
                except asyncio.CancelledError:
                    log("Stream reader cancelled.")
                    raise
                except Exception as exc:
                    log(f"Stream ended with error: {exc}")
                finally:
                    total_elapsed = time.monotonic() - start_time
                    log(
                        f"Stream reader stopping (frames={frame_count}, elapsed={total_elapsed:.1f}s, "
                        f"connectionState={pc.connectionState}, coalesced_before_ui={coalesced_before_ui})."
                    )
                    await _cleanup_peer(pc)
                    _notifyDisconnected()

            task = asyncio.create_task(read_frames())
            _track_tasks.add(task)
            task.add_done_callback(_track_tasks.discard)

        elif track.kind == "audio":
            log("Audio track received.")

            async def read_audio_frames():
                frame_timeout = SCREEN_CAST.FRAME_TIMEOUT_SECONDS
                frame_count = 0
                start_time = time.monotonic()
                try:
                    while True:
                        try:
                            frame = await asyncio.wait_for(track.recv(), timeout=frame_timeout)
                        except asyncio.TimeoutError:
                            log(
                                f"No audio frames received within {frame_timeout}s; "
                                "stopping audio track reader."
                            )
                            break

                        frame_count += 1
                        submitAudioFrame(frame)
                except asyncio.CancelledError:
                    log("Audio stream reader cancelled.")
                    raise
                except Exception as exc:
                    log(f"Audio stream ended with error: {exc}")
                finally:
                    elapsed = time.monotonic() - start_time
                    log(
                        "Audio stream reader stopping "
                        f"(frames={frame_count}, elapsed={elapsed:.1f}s, "
                        f"connectionState={pc.connectionState})."
                    )

            task = asyncio.create_task(read_audio_frames())
            _track_tasks.add(task)
            task.add_done_callback(_track_tasks.discard)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log(f"Connection state changed: {pc.connectionState}")
        if pc.connectionState in ("failed", "closed", "disconnected"):
            await _cleanup_peer(pc)
            _notifyDisconnected()

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        log(f"ICE connection state changed: {pc.iceConnectionState}")

    @pc.on("signalingstatechange")
    def on_signalingstatechange():
        log(f"Signaling state changed: {pc.signalingState}")

    await pc.setRemoteDescription(offer)
    log(f"Remote description set (type={offer.type}).")
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    await _wait_for_ice_gathering_complete(pc, SCREEN_CAST.ICE_GATHER_TIMEOUT_SECONDS)
    answer_candidates = _count_sdp_candidates(pc.localDescription.sdp)
    log(f"Local description created (type={pc.localDescription.type}).")
    log(f"Answer metadata: candidate_count={answer_candidates}.")

    return web.Response(
        content_type="application/json",
        text=json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }),
    )


async def on_shutdown(screenCastServer):
    log(f"Server shutting down, closing peer connections... (count={len(pcs)})")
    for task in list(_track_tasks):
        task.cancel()
    if _track_tasks:
        await asyncio.gather(*list(_track_tasks), return_exceptions=True)
    coros = [_cleanup_peer(pc) for pc in list(pcs)]
    await asyncio.gather(*coros)
    pcs.clear()
    global active_pc
    active_pc = None
    _notifyDisconnected()


async def status(request):
    busy = active_pc is not None and active_pc.connectionState not in ("closed", "failed")
    return web.json_response({"available": not busy})


async def power_status(request):
    # Reachable only once this module is serving, so the TV is on by construction.
    return web.json_response({"on": True})


async def capture_settings(request):
    # The web sender consumes adaptive policy from this endpoint so quality
    # behavior remains centralized and consistent across clients.
    return web.json_response({
        "width": SCREEN_CAST.CAPTURE_WIDTH,
        "height": SCREEN_CAST.CAPTURE_HEIGHT,
        "frameRate": SCREEN_CAST.CAPTURE_FRAME_RATE,
        "iceServers": [{"urls": url} for url in SCREEN_CAST.ICE_SERVERS],
        "adaptLowFpsThreshold": SCREEN_CAST.ADAPT_LOW_FPS_THRESHOLD,
        "adaptLowSampleWindow": SCREEN_CAST.ADAPT_LOW_SAMPLE_WINDOW,
        "adaptLowSampleRequired": SCREEN_CAST.ADAPT_LOW_SAMPLE_REQUIRED,
        "adaptRecoveryFpsThreshold": SCREEN_CAST.ADAPT_RECOVERY_FPS_THRESHOLD,
        "adaptRecoverySampleWindow": SCREEN_CAST.ADAPT_RECOVERY_SAMPLE_WINDOW,
        "adaptRecoverySampleRequired": SCREEN_CAST.ADAPT_RECOVERY_SAMPLE_REQUIRED,
        "adaptDowngradeCooldownSeconds": SCREEN_CAST.ADAPT_DOWNGRADE_COOLDOWN_SECONDS,
        "adaptUpgradeCooldownSeconds": SCREEN_CAST.ADAPT_UPGRADE_COOLDOWN_SECONDS,
        "adaptMinWidth": SCREEN_CAST.ADAPT_MIN_WIDTH,
        "adaptMinHeight": SCREEN_CAST.ADAPT_MIN_HEIGHT,
        "adaptMaxWidth": SCREEN_CAST.ADAPT_MAX_WIDTH,
        "adaptMaxHeight": SCREEN_CAST.ADAPT_MAX_HEIGHT,
        "degradationPreference": SCREEN_CAST.DEGRADATION_PREFERENCE,
        "bitrateMaxBps1080p": SCREEN_CAST.BITRATE_MAX_BPS_1080P,
        "bitrateMinBps1080p": SCREEN_CAST.BITRATE_MIN_BPS_1080P,
        "bitrateMaxBps720p": SCREEN_CAST.BITRATE_MAX_BPS_720P,
        "bitrateMinBps720p": SCREEN_CAST.BITRATE_MIN_BPS_720P,
        "audioEnabled": SCREEN_CAST.AUDIO_ENABLED,
        "receiverDrainTimeoutSeconds": SCREEN_CAST.RECEIVER_DRAIN_TIMEOUT_SECONDS,
    })


screenCastServer = web.Application()
screenCastServer.on_shutdown.append(on_shutdown)
screenCastServer.router.add_get("/", index)
screenCastServer.router.add_get("/cast", cast)
screenCastServer.router.add_get("/{filename:.*\\.(js|css|html|json|map|svg|png|jpg|jpeg|gif|webp)}", serve_static_file)
screenCastServer.router.add_post("/offer", offer)
screenCastServer.router.add_get("/status", status)
screenCastServer.router.add_get("/power-status", power_status)
screenCastServer.router.add_get("/capture-settings", capture_settings)


_runner = None
_site = None

async def startScreenCastServer(host=SCREEN_CAST.HOST, port=SCREEN_CAST.PORT):
    global _runner, _site

    if _runner is not None:
        return

    _runner, _site = await start_site(screenCastServer, host, port, LOG_PREFIX)

async def stopScreenCastServer():
    global _runner, _site

    await stop_site(_runner, _site)
    _runner = None
    _site = None