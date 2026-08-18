from PyQt5.QtCore import QCoreApplication

from app_logging import get_adapter
from webserver.screen_cast import stopScreenCastServer
from audio_playback import stopAudioPlayback


logger = get_adapter("teardown", "teardown")
_shutdown_started = False


def reset_shutdown_state():
    global _shutdown_started
    _shutdown_started = False


async def teardown_app(projector_interface=None, quit_app=False):
    global _shutdown_started

    if _shutdown_started:
        return

    _shutdown_started = True

    try:
        if projector_interface is not None:
            try:
                await projector_interface.off()
            except Exception as exc:
                logger.exception("Projector shutdown failed", exc, component="projector")

        try:
            await stopAudioPlayback()
        except Exception as exc:
            logger.exception("Audio playback shutdown failed", exc, component="audio")

        try:
            await stopScreenCastServer()
        except Exception as exc:
            logger.exception("Screen cast shutdown failed", exc, component="screencast")

        if quit_app:
            QCoreApplication.quit()
    except Exception as exc:
        logger.exception("Teardown failed", exc)
