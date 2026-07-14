print("[ir_interface] Importing infrared interface...")

import subprocess

from globals import DEVICE


LOG_PREFIX = "[ir_interface]"


def log(message):
    print(f"{LOG_PREFIX} {message}")

class IRInterface:
    def __init__(self, *args, **kwargs):
        log(f"Initializing IR interface (raspberry_pi={DEVICE.IS_RASPBERRY_PI}).")
        self._can_send_ir = DEVICE.IS_RASPBERRY_PI
    
    def send(self, data):
        if self._can_send_ir:
            command = ["irsend", "SEND_ONCE", "Projector", data]
            log(f"Sending IR command: {command!r}")
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=False)
            except Exception as exc:
                log(f"Failed to execute {command!r}: {exc}")
                return

            if result.returncode != 0:
                stderr = result.stderr.strip()
                stdout = result.stdout.strip()
                if stderr:
                    log(f"Command failed with return code {result.returncode}: {stderr}")
                elif stdout:
                    log(f"Command failed with return code {result.returncode}: {stdout}")
                else:
                    log(f"Command failed with return code {result.returncode} and no output.")
                return

            if result.stdout.strip():
                log(f"Command output: {result.stdout.strip()}")

irInterface = IRInterface()