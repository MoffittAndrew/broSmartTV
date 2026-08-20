"""Phase 0 feasibility spike - run this manually ON THE PI, not as part of the app.

See broSmartTV/WEB_INTEGRATION.md for the full write-up of the web integration this
validates (architecture, navigation, keyboard, DRM/Widevine).

Validates the three prerequisites the QWebEngineView redesign depends on:
1. QWebEngineView actually renders/composites under QT_QPA_PLATFORM=eglfs.
2. Proprietary codecs (H.264) are enabled in the installed QtWebEngine build.
3. A Widevine CDM binary for the Pi's architecture enables real DRM playback.

Usage on the Pi (from /bro/app, using the shared venv):
    # REQUIRED on Pi 5: the default kernel (bcm2712_defconfig) uses 16K pages, but Qt5
    # WebEngine's bundled Chromium hardcodes 4K page-size assumptions and crashes with
    # "page_allocator_internals_posix.h Check failed: Invalid argument (22)" under it.
    # launcher/install-bro's ensure_4k_page_kernel now does this automatically (adds
    # kernel=kernel8.img to /boot/firmware/config.txt, needs a reboot to take effect) -
    # confirm with `getconf PAGESIZE` (should print 4096, not 16384). See
    # https://github.com/raspberrypi/bookworm-feedback/issues/107.
    export QT_QPA_PLATFORM=eglfs
    export QT_QPA_EGLFS_KMS_CONFIG=/bro/app/launcher/eglfs_kms_conf.json
    # DevTools binds to loopback only; for LAN access either tunnel with
    # `ssh -L 9222:localhost:9222 bro@<pi-ip>` or add --remote-debugging-address=0.0.0.0 below.
    # export QTWEBENGINE_CHROMIUM_FLAGS=--remote-debugging-address=0.0.0.0
    # Only needed once a Widevine CDM binary has been sourced for this device's arch - launcher/launch
    # sets this automatically from /bro/widevine/libwidevinecdm.so once that file exists there.
    # export QTWEBENGINE_CHROMIUM_FLAGS=--widevine-path=/bro/widevine/libwidevinecdm.so
    /bro/.venv/bin/python webengine_pi_spike.py

What to check manually once it's running:
- Does the page actually paint (not a black/blank screen)? Confirms eglfs rendering works.
- Does the small red box in the corner (a plain always-on-top-less QLabel, raised the same
  way InputInterface now stacks) render ABOVE the web content? Confirms Qt-native stacking
  works for a real QWebEngineView the way it never reliably could for an embedded foreign HWND.
- Open browser DevTools (this script enables remote debugging) from another machine at
  http://<pi-ip>:9222 and check chrome://gpu plus play a known H.264 test video.
- Load a DRM test page (e.g. https://demo.castlabs.com/ or https://bitmovin.com/demos/drm)
  and confirm playback succeeds once QTWEBENGINE_CHROMIUM_FLAGS points at a sourced CDM.
"""

import os
import sys

os.environ.setdefault("QTWEBENGINE_REMOTE_DEBUGGING", "8080")

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication, QLabel, QStackedLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView

TEST_URL = "https://demo.castlabs.com/"


def main():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("QWebEngineView / eglfs spike")
    layout = QStackedLayout(window)
    layout.setStackingMode(QStackedLayout.StackAll)

    view = QWebEngineView()
    view.load(QUrl(TEST_URL))
    layout.addWidget(view)

    marker = QLabel("STACKING OK", window)
    marker.setAutoFillBackground(True)
    palette = marker.palette()
    palette.setColor(QPalette.Window, QColor("red"))
    palette.setColor(QPalette.WindowText, QColor("white"))
    marker.setPalette(palette)
    marker.setFixedSize(220, 60)
    layout.addWidget(marker)
    marker.show()
    marker.raise_()

    window.showFullScreen()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
