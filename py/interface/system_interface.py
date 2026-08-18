from app_logging import get_adapter

logger = get_adapter("system", "system")
logger.info("Importing system interface...")

import asyncio
import subprocess

from PyQt5.QtCore import QCoreApplication

from globals import DEVICE
from launch_signals import (
    EXIT_CODE_REBOOTING,
    request_exit_code as _request_exit_code_default,
    request_skip_standby as _request_skip_standby_default,
)
from teardown import teardown_app


class SystemInterface:
    """Restart/reboot actions that deliberately skip projector shutoff (see teardown.teardown_app)."""

    def __init__(
        self,
        teardown=None,
        async_command_runner=None,
        quit_app=None,
        request_skip_standby=None,
        request_exit_code=None,
        is_raspberry_pi=None,
        *args,
        **kwargs,
    ):
        self.__teardown = teardown or teardown_app
        self.__async_command_runner = async_command_runner or self._run_async_command
        self.__quit_app = quit_app or QCoreApplication.quit
        self.__request_skip_standby = request_skip_standby or _request_skip_standby_default
        self.__request_exit_code = request_exit_code or _request_exit_code_default
        self.__is_raspberry_pi = DEVICE.IS_RASPBERRY_PI if is_raspberry_pi is None else is_raspberry_pi

    async def _run_async_command(self, command):
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return subprocess.CompletedProcess(
            command,
            process.returncode if process.returncode is not None else 1,
            stdout.decode(errors="replace"),
            stderr.decode(errors="replace"),
        )

    async def restart_app(self):
        logger.info("Restarting app...", category="system")
        # Next launch.py run should boot straight into the app instead of standby.
        self.__request_skip_standby()
        # No projector_interface passed: projector stays on. Quitting relies on the
        # Pi launcher's bash loop (or local dev's aboutToQuit hook) to bring the app back.
        await self.__teardown(quit_app=True)

    async def reboot_device(self):
        logger.info("Rebooting device...", category="system")
        self.__request_skip_standby()
        # A graceful self-quit returns 0 normally, which would make the bash loop restart
        # us mid-reboot; request 201 so it recognizes this and doesn't race the real shutdown.
        self.__request_exit_code(EXIT_CODE_REBOOTING)
        # Stop services but don't quit yet - we still need this process alive to await the command below.
        await self.__teardown(quit_app=False)

        if not self.__is_raspberry_pi:
            logger.warning("Skipping reboot command on non-Raspberry-Pi device.", category="system")
        else:
            try:
                result = await self.__async_command_runner(["sudo", "shutdown", "-r", "now"])
            except Exception as exc:
                logger.exception("Failed to run reboot command", exc, component="reboot")
            else:
                if result.returncode != 0:
                    logger.error(
                        "Reboot command failed",
                        returncode=result.returncode,
                        stderr=result.stderr.strip(),
                    )
                else:
                    logger.info("Reboot command issued.", category="system")

        self.__quit_app()


systemInterface = SystemInterface()
