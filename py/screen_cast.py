# this code was written by chatgpt (I gave up)
# Launches the screen cast (via RTC) webserver
# TODO stream screen data to the smart TV

print("Importing screen cast server...")

import os
import asyncio
import json
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder
import cv2

pcs = set()
active_pc = None  # only one active peer connection at a time

async def index(request):
    return web.FileResponse(os.path.dirname(__file__) + "\\..\\index.html")

async def offer(request):
    global active_pc

    # If a stream is already active, reject new connection
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
    active_pc = pc  # mark as current active connection
    print("New PeerConnection created")

    @pc.on("track")
    def on_track(track):
        print(f"Track received: {track.kind}")

        if track.kind == "video":
            recorder = MediaRecorder("display.mp4")
            recorder.addTrack(track)
            asyncio.ensure_future(recorder.start())

            async def show_frames():
                while True:
                    try:
                        frame = await track.recv()
                        img = frame.to_ndarray(format="bgr24")
                        cv2.imshow("Remote Screen", img)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            break
                    except Exception as e:
                        print("Stream ended:", e)
                        break

                print("Closing OpenCV window")
                cv2.destroyAllWindows()
                await recorder.stop()
                await pc.close()
                if pc in pcs:
                    pcs.discard(pc)
                if pc == active_pc:
                    globals()["active_pc"] = None

            asyncio.ensure_future(show_frames())

        @track.on("ended")
        async def on_ended():
            print("Track ended by client")
            await recorder.stop()
            await pc.close()
            if pc in pcs:
                pcs.discard(pc)
            if pc == active_pc:
                globals()["active_pc"] = None
            cv2.destroyAllWindows()

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state changed: {pc.connectionState}")
        if pc.connectionState in ("failed", "closed", "disconnected"):
            print("Connection closed, cleaning up.")
            await pc.close()
            if pc in pcs:
                pcs.discard(pc)
            if pc == active_pc:
                globals()["active_pc"] = None
            cv2.destroyAllWindows()

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
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()
    globals()["active_pc"] = None
    cv2.destroyAllWindows()

async def status(request):
    busy = active_pc is not None and active_pc.connectionState not in ("closed", "failed")
    return web.json_response({"available": not busy})

screenCastServer = web.Application()
screenCastServer.on_shutdown.append(on_shutdown)
screenCastServer.router.add_get("/", index)
screenCastServer.router.add_post("/offer", offer)
screenCastServer.router.add_get("/status", status)

async def startScreenCastServer():
    await web.run_app(screenCastServer, host="0.0.0.0", port=8080)