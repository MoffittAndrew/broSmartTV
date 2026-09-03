from app_logging import get_adapter

logger = get_adapter("ir", "projector")
logger.info("Importing infrared interface...")

import subprocess

from globals import DEVICE


def log(message):
    logger.info(message)

class IRInterface:
    def __init__(self, *args, **kwargs):
        log(f"Initializing IR interface (raspberry_pi={DEVICE.IS_RASPBERRY_PI}).")
        self._can_send_ir = DEVICE.IS_RASPBERRY_PI
    
    def send(self, device, data):
        if self._can_send_ir:
            command = ["irsend", "SEND_ONCE", device, data]
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