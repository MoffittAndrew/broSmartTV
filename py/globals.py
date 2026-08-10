# System settings

print("Importing globals...")

import os
import platform
import socket
from PyQt5.QtCore import Qt

PATH = os.path.dirname(__file__) + "/../"


def _screen_cast_tls_paths():
    cert_path = os.getenv("SCREEN_CAST_SSL_CERT")
    key_path = os.getenv("SCREEN_CAST_SSL_KEY")

    if cert_path and key_path:
        return cert_path, key_path

    default_cert_path = os.path.join(PATH, "certs", "screen-cast.crt")
    default_key_path = os.path.join(PATH, "certs", "screen-cast.key")
    if os.path.exists(default_cert_path) and os.path.exists(default_key_path):
        return default_cert_path, default_key_path

    return None, None


def _read_system_file(path, **kwargs):
    try:
        with open(path, "r", **kwargs) as f:
            return f.read().lower()
    except OSError:
        return ""


def _discover_lan_ipv4():
    """Return a best-effort private LAN IPv4 address, or None if unavailable."""
    candidates = set()

    # Hostname resolution can be stale/incomplete, but still useful when valid.
    try:
        candidates.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass

    # UDP connect trick picks the outbound interface without sending traffic.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            candidates.add(sock.getsockname()[0])
        finally:
            sock.close()
    except OSError:
        pass

    candidates = [ip for ip in candidates if ip and not ip.startswith("127.")]

    # Prefer the common home-LAN range first.
    for ip in candidates:
        if ip.startswith("192.168."):
            return ip

    # Then accept other RFC1918 private ranges.
    for ip in candidates:
        if ip.startswith("10."):
            return ip
        if ip.startswith("172."):
            parts = ip.split(".")
            if len(parts) >= 2:
                try:
                    second = int(parts[1])
                except ValueError:
                    continue
                if 16 <= second <= 31:
                    return ip

    return None


class DEVICE:
    IS_LINUX = platform.system() == "Linux"
    OS_RELEASE = _read_system_file("/etc/os-release", encoding="utf-8") if IS_LINUX else ""
    IS_DEBIAN = "id=debian" in OS_RELEASE or "id_like=debian" in OS_RELEASE
    MODEL = _read_system_file("/proc/device-tree/model", encoding="utf-8", errors="ignore") if IS_LINUX else ""
    IS_RASPBERRY_PI = "raspberry pi" in MODEL

class DISPLAY:
    WIDTH = 1920
    HEIGHT = 1080
    WINDOW_TITLE = "bro is literally a smart tv"

class WIFI:
    KNOWN_NETWORKS_FILE = os.path.join(PATH, "known_networks.json")

class _BUTTON:
    MIN_WIDTH = 200
    MIN_HEIGHT = 100
    TEXT_SIZE = 60
    ROUNDNESS = 30
    COLOR = Qt.white
    COLOR_DISABLED = Qt.gray
    BORDER_THICKNESS = 3
    BG_COLOR = Qt.black

class _NAVBAR:
    BUTTON_WIDTH = 300
    BUTTON_HEIGHT = 100

class _TILE:
    WIDTH = 400
    HEIGHT = 300
    EDIT_NAME_TEXT = "edit url"
    EDIT_IMG_TEXT = "edit image"
    EDIT_INPUT_TEXT = "edit input channel"
    EDIT_URL_TEXT = "edit url"
    TOGGLE_MUSIC_TEXT = "music site?"
    TOGGLE_SEARCH_TEXT = "has search feature?"
    TOGGLE_PIRATE_TEXT = "pirate site?"

class _TILEGRID:
    COLUMNS = 5

class _LAYOUT_SPACING:
    TIGHT = 10
    NORMAL = 24
    WIDE = 30

class _LAYOUT_MARGINS:
    COMPACT = (40, 40, 40, 40)
    STANDARD = (80, 60, 80, 60)
    OVERLAY = (80, 40, 80, 40)

class GUI:
    BG_COLOR = Qt.black
    INPUT_INTERFACE_COLOR = Qt.red
    BUTTON = _BUTTON
    NAVBAR = _NAVBAR
    TILE = _TILE
    TILEGRID = _TILEGRID
    SPACING = _LAYOUT_SPACING
    MARGINS = _LAYOUT_MARGINS

class _IR_CODES:
    ON = "KEY_POWER"
    OFF = "KEY_POWER_OFF"
    SELECT = "KEY_ENTER"
    NAV_UP = "KEY_UP"
    NAV_RIGHT = "KEY_RIGHT"
    NAV_DOWN = "KEY_DOWN"
    NAV_LEFT = "KEY_LEFT"
    MENU = "KEY_MENU"
    RETURN = "KEY_ESC"
    VOL_UP = "KEY_VOLUMEUP"
    VOL_DOWN = "KEY_VOLUMEDOWN"
    SRC_ = "KEY_SRC_"

class _INPUT_CHANNELS:
    SEARCH = "SEARCH"
    HDMI = "HDMI"
    VGA = "VGA"
    COMPONENT = "COMPONENT"

class PROJECTOR:
    CODES = _IR_CODES
    CHANNELS = _INPUT_CHANNELS
    CHANNEL_SWITCH_DELAY = 5
    INPUT_DELAY = 0.2

class REMOTE:
    NAME = "bro-ito"
    SERVICE_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x1849)
    CHARACTERISTIC_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(0x2BA5)
    CHECK_ALIVE_INTERVAL = 5
    SCAN_TIMEOUT = 300

class _INPUT_MODES:
    GUI = 0
    PROJECTOR = 1
    WEB = 2
    OTHER = 3

class INPUT:
    MODES = _INPUT_MODES
    RELEASED_PREFIX = "RELEASED_"
    NAV_PREFIX = "NAV_"
    HOME = "HOME"
    POWER = "POWER"
    SELECT = "SELECT"
    NAV_UP = NAV_PREFIX + "UP"
    NAV_RIGHT = NAV_PREFIX + "RIGHT"
    NAV_DOWN = NAV_PREFIX + "DOWN"
    NAV_LEFT = NAV_PREFIX + "LEFT"
    MENU = "MENU"
    RETURN = "RETURN"
    VOL_UP = "VOL_UP"
    VOL_DOWN = "VOL_DOWN"
    MIC = "MIC"
    LOOKUP = {
        POWER: Qt.Key_Q,
        HOME: Qt.Key_Space,
        SELECT: Qt.Key_Return,
        NAV_UP: Qt.Key_Up,
        NAV_RIGHT: Qt.Key_Right,
        NAV_DOWN: Qt.Key_Down,
        NAV_LEFT: Qt.Key_Left,
        MENU: Qt.Key_Tab,
        RETURN: Qt.Key_Escape,
    }

class SCREEN_CAST:
    IP = _discover_lan_ipv4()
    HOST = "0.0.0.0"
    PORT = 8080
    CAPTURE_WIDTH = 1920
    CAPTURE_HEIGHT = 1080
    CAPTURE_FRAME_RATE = 30

    # Adaptive downshift trigger: if FPS remains below 15 for 10 consecutive
    # one-second samples, prioritize smoothness over fidelity by switching to
    # the 720p floor profile.
    ADAPT_LOW_FPS_THRESHOLD = 15
    ADAPT_LOW_SAMPLE_WINDOW = 10
    ADAPT_LOW_SAMPLE_REQUIRED = 10

    # Adaptive recovery trigger: if floor quality is consistently healthy,
    # return to 1080p once FPS is at least 25 for roughly 15 seconds.
    # up to 1080p to avoid oscillating quality under marginal conditions.
    ADAPT_RECOVERY_FPS_THRESHOLD = 25
    ADAPT_RECOVERY_SAMPLE_WINDOW = 15
    ADAPT_RECOVERY_SAMPLE_REQUIRED = 13

    # Directional cooldowns are intentionally asymmetric: upgrades wait longer
    # than downgrades so FPS protection reacts quickly while quality recovery
    # remains conservative.
    ADAPT_DOWNGRADE_COOLDOWN_SECONDS = 10
    ADAPT_UPGRADE_COOLDOWN_SECONDS = 20

    # Hard bounds for this phase: never below 720p and never above 1080p.
    ADAPT_MIN_WIDTH = 1280
    ADAPT_MIN_HEIGHT = 720
    ADAPT_MAX_WIDTH = 1920
    ADAPT_MAX_HEIGHT = 1080

    # Sender policy is centralized here so browser-side WebRTC tuning remains
    # reproducible across sessions and Pi deployments.
    DEGRADATION_PREFERENCE = "maintain-framerate"
    BITRATE_MAX_BPS_1080P = 5_000_000
    BITRATE_MIN_BPS_1080P = 0
    BITRATE_MAX_BPS_720P = 2_800_000
    BITRATE_MIN_BPS_720P = 0

    # If the receiver loop is behind, drain any immediately available backlog
    # and forward only the freshest decoded frame to avoid catch-up bursts.
    RECEIVER_DRAIN_TIMEOUT_SECONDS = 0.001

    FRAME_TIMEOUT_SECONDS = 10
    FRAME_LOG_INTERVAL_SECONDS = 5
    ICE_GATHER_TIMEOUT_SECONDS = 8
    ICE_SERVERS = [
        "stun:stun.l.google.com:19302",
        "stun:stun1.l.google.com:19302",
    ]
    SSL_CERT, SSL_KEY = _screen_cast_tls_paths()

class WEB:
    CHROMIUM_PATH = "/usr/lib/chromium-browser/chromedriver"
    MAX_GET_WINDOW_TRIES = 30