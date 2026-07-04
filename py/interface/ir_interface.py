print("Importing infrared interface...")

import os
import platform


def _is_raspberry_pi_debian():
    if platform.system() != "Linux":
        return False

    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            os_release = f.read().lower()
    except OSError:
        return False

    is_debian = "id=debian" in os_release or "id_like=debian" in os_release
    if not is_debian:
        return False

    try:
        with open("/proc/device-tree/model", "r", encoding="utf-8", errors="ignore") as f:
            return "raspberry pi" in f.read().lower()
    except OSError:
        return False

class IRInterface:
    def __init__(self, *args, **kwargs):
        self._can_send_ir = _is_raspberry_pi_debian()
    
    def send(self, data):
        if self._can_send_ir:
            os.system(f"irsend SEND_ONCE Projector {data}")

irInterface = IRInterface()