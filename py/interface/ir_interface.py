from app_logging import get_adapter

logger = get_adapter("ir", "startup")
logger.info("Importing infrared interface...")

import subprocess

from globals import DEVICE

class IRInterface:
    def __init__(self, *args, **kwargs):
        logger.info(f"Initializing IR interface (raspberry_pi={DEVICE.IS_RASPBERRY_PI}).")
        self._can_send_ir = DEVICE.IS_RASPBERRY_PI
    
    def send(self, device, data):
        if self._can_send_ir:
            command = ["irsend", "SEND_ONCE", device, data]
            logger.info(f"Sending IR command: {command!r}", category=device)
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=False)
            except Exception as exc:
                logger.error(f"Failed to execute {command!r}: {exc}", category=device)
                return

            if result.returncode != 0:
                stderr = result.stderr.strip()
                stdout = result.stdout.strip()
                if stderr:
                    logger.error(f"Command failed with return code {result.returncode}: {stderr}", category=device)
                elif stdout:
                    logger.error(f"Command failed with return code {result.returncode}: {stdout}", category=device)
                else:
                    logger.error(f"Command failed with return code {result.returncode} and no output.", category=device)
                return

            if result.stdout.strip():
                logger.error(f"Command output: {result.stdout.strip()}", category=device)

irInterface = IRInterface()