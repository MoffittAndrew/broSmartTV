# this code was written by AI (I gave up)
# Launches the screen cast (via RTC) webserver and forwards video frames to the Qt UI

from app_logging import get_adapter

logger = get_adapter("screencast", "screencast")
logger.info("Importing screen cast server...")

import os
import asyncio
import json
import time
import weakref
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from globals import PATH, SCREEN_CAST
from audio_playback import submitAudioFrame, stopAudioPlayback
from webserver.webserver_utils import start_site, stop_site, build_static_file_handler
from webserver.logs_routes import add_routes as add_logs_routes, reset_stream_shutdown
from webserver import remote_control
from webserver import webdebug_routes
from webserver import aioice_compat

aioice_compat.apply()

pcs = set()
active_pc = None  # only one active peer connection at a time
_track_tasks = set()
_cleaning_peers = set()
_cleaned_peers = weakref.WeakSet()
_keyframe_tasks = {}

_frame_handler = None
_connection_handler = None
_disconnect_handler = None


def log(message, level="INFO", **fields):
    return logger.log(level, message, **fields)


def _peer_state_fields(pc):
    return {
        "connection_state": pc.connectionState,
        "ice_connection_state": pc.iceConnectionState,
        "ice_gathering_state": pc.iceGatheringState,
        "signaling_state": pc.signalingState,
    }


def _log_peer_state(pc, message, level="INFO", **fields):
    fields.update(_peer_state_fields(pc))
    return logger.log(level, message, **fields)


def _exception_summary(exc):
    return str(exc).strip() or "<no exception message>"


def _log_stream_exception(pc, message, exc, **fields):
    fields.update(_peer_state_fields(pc))
    message = (
        f"{message} exception_type={type(exc).__name__}; "
        f"exception_message={_exception_summary(exc)}"
    )
    if type(exc).__name__ == "MediaStreamError" and pc.connectionState in ("closed", "failed", "disconnected"):
        fields.update({
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        })
        return logger.warning(message, **fields)
    return logger.exception(message, exc, **fields)


def setFrameHandler(callback):
    global _frame_handler
    _frame_handler = callback


def setConnectionHandler(callback):
    global _connection_handler
    _connection_handler = callback


def setDisconnectHandler(callback):
    global _disconnect_handler
    _disconnect_handler = callback


def _notifyFrame(frame, arrival_time=None):
    if _frame_handler is not None:
        _frame_handler(frame, arrival_time)


def _notifyConnected():
    if _connection_handler is not None:
        _connection_handler()


def _notifyDisconnected():
    if _disconnect_handler is not None:
        _disconnect_handler()


def _receiver_for_track(pc, track):
    for receiver in pc.getReceivers():
        if receiver.track is track:
            return receiver
    return None


def _receiver_media_ssrcs(receiver):
    """Return active media SSRCs for aiortc's receiver-side PLI request."""
    active_ssrcs = getattr(receiver, "_RTCRtpReceiver__active_ssrc", None)
    if isinstance(active_ssrcs, dict):
        return list(active_ssrcs)

    remote_streams = getattr(receiver, "_RTCRtpReceiver__remote_streams", None)
    if isinstance(remote_streams, dict):
        return list(remote_streams)

    return []


async def _request_keyframe(pc, track, reason, request_times):
    if pc.connectionState in ("closed", "failed", "disconnected"):
        return False

    now = time.monotonic()
    window_seconds = SCREEN_CAST.KEYFRAME_REQUEST_WINDOW_SECONDS
    request_times[:] = [timestamp for timestamp in request_times if now - timestamp < window_seconds]
    if len(request_times) >= SCREEN_CAST.KEYFRAME_REQUEST_MAX_PER_WINDOW:
        return False

    receiver = _receiver_for_track(pc, track)
    request_pli = getattr(receiver, "_send_rtcp_pli", None)
    if request_pli is None:
        log(
            "Keyframe recovery unavailable: receiver does not support RTCP PLI.",
            level="WARNING",
            reason=reason,
        )
        return False

    media_ssrcs = _receiver_media_ssrcs(receiver)
    if not media_ssrcs:
        return False

    for media_ssrc in media_ssrcs:
        await request_pli(media_ssrc)

    request_times.append(now)
    log(
        "Requested keyframe for screen-cast recovery.",
        reason=reason,
        request_count=len(request_times),
        media_ssrc_count=len(media_ssrcs),
    )
    return True


async def _run_keyframe_watchdog(pc, track):
    request_times = []
    try:
        await asyncio.sleep(SCREEN_CAST.KEYFRAME_REQUEST_STARTUP_GRACE_SECONDS)
        while pc.connectionState not in ("closed", "failed", "disconnected"):
            await _request_keyframe(pc, track, "periodic decoder recovery", request_times)
            await asyncio.sleep(SCREEN_CAST.KEYFRAME_REQUEST_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("Keyframe recovery watchdog failed", exc, reason="watchdog")


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


async def _cleanup_peer(pc, reason="unspecified", initiated_by="unknown"):
    global active_pc

    if pc in _cleaning_peers or pc in _cleaned_peers:
        return

    _cleaning_peers.add(pc)
    _cleaned_peers.add(pc)
    cleanup_fields = {
        "cleanup_reason": reason,
        "cleanup_initiated_by": initiated_by,
        **_peer_state_fields(pc),
    }
    _log_peer_state(pc, "Peer cleanup started.", **cleanup_fields)

    try:
        keyframe_task = _keyframe_tasks.pop(pc, None)
        if keyframe_task is not None:
            keyframe_task.cancel()

        if pc in pcs:
            pcs.discard(pc)

        if active_pc == pc:
            active_pc = None

        try:
            await stopAudioPlayback()
        except Exception as exc:
            logger.exception(
                "Audio playback cleanup failed "
                f"exception_type={type(exc).__name__}; "
                f"exception_message={_exception_summary(exc)}",
                exc,
                **_peer_state_fields(pc),
            )

        try:
            await pc.close()
            _log_peer_state(
                pc,
                "Peer connection closed.",
                cleanup_reason=reason,
                cleanup_initiated_by=initiated_by,
            )
        except Exception as exc:
            logger.exception(
                "Peer cleanup close failed "
                f"exception_type={type(exc).__name__}; "
                f"exception_message={_exception_summary(exc)}",
                exc,
                **_peer_state_fields(pc),
            )
    finally:
        _cleaning_peers.discard(pc)


WEBPAGES_DIR = os.path.join(PATH, "webpages")


async def index(request):
    return web.HTTPFound("/remote")


async def cast(request):
    return web.FileResponse(os.path.join(WEBPAGES_DIR, "cast.html"))


def _normalize_next_path(next_path):
    if (
        isinstance(next_path, str)
        and next_path.startswith("/")
        and not next_path.startswith("//")
    ):
        return next_path
    return "/cast"


async def standby(request):
    # Only single-slash paths reach this redirect; protocol-relative URLs fall back to /cast.
    # snyk ignore:python/OR
    return web.HTTPFound(_normalize_next_path(request.query.get("next")))


serve_static_file = build_static_file_handler(WEBPAGES_DIR)


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

                        if frame_count == 1:
                            log(f"First video frame received after {now - start_time:.2f}s.")

                        if now - last_log_time >= log_interval:
                            elapsed = max(now - start_time, 1e-6)
                            avg_fps = frame_count / elapsed
                            log(
                                f"Frame stats: frames={frame_count}, elapsed={elapsed:.1f}s, "
                                f"avg_fps={avg_fps:.1f}."
                            )
                            last_log_time = now

                        # Send raw frames to the UI callback so receiver-side
                        # coalescing can drop stale frames before expensive
                        # RGB numpy conversion is performed.
                        _notifyFrame(frame, now)
                except asyncio.CancelledError:
                    log("Stream reader cancelled.")
                    raise
                except Exception as exc:
                    _log_stream_exception(
                        pc,
                        "Video stream reader ended with an exception.",
                        exc,
                        track_kind="video",
                        frame_count=frame_count,
                        elapsed_seconds=round(time.monotonic() - start_time, 1),
                    )
                finally:
                    total_elapsed = time.monotonic() - start_time
                    log(
                        f"Stream reader stopping (frames={frame_count}, elapsed={total_elapsed:.1f}s, "
                        f"connectionState={pc.connectionState})."
                    )
                    await _cleanup_peer(
                        pc,
                        reason="video_reader_finished",
                        initiated_by="video_reader",
                    )
                    _notifyDisconnected()

            task = asyncio.create_task(read_frames())
            _track_tasks.add(task)
            task.add_done_callback(_track_tasks.discard)

            keyframe_task = asyncio.create_task(_run_keyframe_watchdog(pc, track))
            _keyframe_tasks[pc] = keyframe_task
            keyframe_task.add_done_callback(lambda _: _keyframe_tasks.pop(pc, None))

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
                    _log_stream_exception(
                        pc,
                        "Audio stream reader ended with an exception.",
                        exc,
                        track_kind="audio",
                        frame_count=frame_count,
                        elapsed_seconds=round(time.monotonic() - start_time, 1),
                    )
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
        _log_peer_state(pc, "Connection state changed.", state=pc.connectionState)
        if pc.connectionState in ("failed", "closed", "disconnected"):
            await _cleanup_peer(
                pc,
                reason=f"connection_state_{pc.connectionState}",
                initiated_by="connection_state_callback",
            )
            _notifyDisconnected()

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        _log_peer_state(pc, "ICE connection state changed.", state=pc.iceConnectionState)

    @pc.on("icegatheringstatechange")
    def on_icegatheringstatechange():
        _log_peer_state(pc, "ICE gathering state changed.", state=pc.iceGatheringState)

    @pc.on("signalingstatechange")
    def on_signalingstatechange():
        _log_peer_state(pc, "Signaling state changed.", state=pc.signalingState)

    negotiation_phase = "set_remote_description"
    try:
        await pc.setRemoteDescription(offer)
        log(f"Remote description set (type={offer.type}).")
        negotiation_phase = "create_answer"
        answer = await pc.createAnswer()
        negotiation_phase = "set_local_description"
        await pc.setLocalDescription(answer)
        negotiation_phase = "ice_gathering"
        await _wait_for_ice_gathering_complete(pc, SCREEN_CAST.ICE_GATHER_TIMEOUT_SECONDS)
        answer_candidates = _count_sdp_candidates(pc.localDescription.sdp)
        log(f"Local description created (type={pc.localDescription.type}).")
        log(f"Answer metadata: candidate_count={answer_candidates}.")
    except Exception as exc:
        logger.exception(
            "Screen cast negotiation failed "
            f"exception_type={type(exc).__name__}; "
            f"exception_message={_exception_summary(exc)}",
            exc,
            phase=negotiation_phase,
            remote=request.remote,
            offer_type=offer.type,
            offer_candidate_count=offer_candidates,
            **_peer_state_fields(pc),
        )
        await _cleanup_peer(
            pc,
            reason=f"negotiation_failed_{negotiation_phase}",
            initiated_by="offer_handler",
        )
        raise

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
    for task in list(_keyframe_tasks.values()):
        task.cancel()
    if _track_tasks:
        await asyncio.gather(*list(_track_tasks), return_exceptions=True)
    if _keyframe_tasks:
        await asyncio.gather(*list(_keyframe_tasks.values()), return_exceptions=True)
    coros = [
        _cleanup_peer(pc, reason="application_shutdown", initiated_by="server_shutdown")
        for pc in list(pcs)
    ]
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
screenCastServer.router.add_get("/standby", standby)
add_logs_routes(screenCastServer)
# Registered before the static-file catch-all below, since some proxied devtools assets end in
# .html/.js and would otherwise be shadowed by that broader pattern.
webdebug_routes.add_routes(screenCastServer)
screenCastServer.router.add_get("/{filename:.*\\.(js|css|html|json|map|svg|png|jpg|jpeg|gif|webp)}", serve_static_file)
screenCastServer.router.add_post("/offer", offer)
screenCastServer.router.add_get("/status", status)
screenCastServer.router.add_get("/power-status", power_status)
screenCastServer.router.add_get("/capture-settings", capture_settings)
remote_control.add_routes(screenCastServer)


_runner = None
_site = None

async def startScreenCastServer(host=SCREEN_CAST.HOST, port=SCREEN_CAST.PORT):
    global _runner, _site

    if _runner is not None:
        return

    reset_stream_shutdown(screenCastServer)
    _runner, _site = await start_site(screenCastServer, host, port, "screencast")

async def stopScreenCastServer():
    global _runner, _site

    await stop_site(_runner, _site)
    _runner = None
    _site = None