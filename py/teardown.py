from PyQt5.QtCore import QCoreApplication

from screen_cast import stopScreenCastServer


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
                print(f"Projector shutdown failed: {exc}")

        try:
            await stopScreenCastServer()
        except Exception as exc:
            print(f"Screen cast shutdown failed: {exc}")

        if quit_app:
            QCoreApplication.quit()
    except Exception as exc:
        print(f"Teardown failed: {exc}")
