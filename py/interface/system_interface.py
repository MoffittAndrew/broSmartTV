from app_logging import get_adapter

logger = get_adapter("system", "system")
logger.info("Importing system interface...")

import asyncio
import subprocess

from PyQt5.QtCore import QCoreApplication

from globals import DEVICE
from launch_signals import (
    request_reboot_pending as _request_reboot_pending_default,
    request_skip_standby as _request_skip_standby_default,
)
from teardown import teardown_app


class SystemInterface:
    """Restart/reboot deliberately skip projector shutoff; shutdown_app() turns it off (see teardown.teardown_app)."""

    def __init__(
        self,
        teardown=None,
        async_command_runner=None,
        quit_app=None,
        request_skip_standby=None,
        request_reboot_pending=None,
        is_raspberry_pi=None,
        projector_interface=None,
        soundbar_interface=None,
        show_shutdown_screen=None,
        config_interface=None,
        *args,
        **kwargs,
    ):
        self.__teardown = teardown or teardown_app
        self.__async_command_runner = async_command_runner or self._run_async_command
        self.__quit_app = quit_app or QCoreApplication.quit
        self.__request_skip_standby = request_skip_standby or _request_skip_standby_default
        self.__request_reboot_pending = request_reboot_pending or _request_reboot_pending_default
        self.__is_raspberry_pi = DEVICE.IS_RASPBERRY_PI if is_raspberry_pi is None else is_raspberry_pi
        # Not available at module-import time; set later via setConfigInterface() (see main.py wiring).
        self.__config_interface = config_interface
        # Not available at module-import time; set later via setProjectorInterface() (see main.py wiring).
        self.__projector_interface = projector_interface
        self.__soundbar_interface = soundbar_interface
        self.__show_shutdown_screen = show_shutdown_screen or self._default_show_shutdown_screen

    def setProjectorInterface(self, projector_interface):
        self.__projector_interface = projector_interface
    
    def setSoundbarInterface(self, soundbar_interface):
        self.__soundbar_interface = soundbar_interface

    def setConfigInterface(self, config_interface):
        self.__config_interface = config_interface

    def _default_show_shutdown_screen(self, msg=None):
        # Lazy import keeps this module's import graph Qt/UI-free for non-GUI callers and tests.
        from ui.gui import MAIN_WINDOW
        MAIN_WINDOW.showShutdownScreen(msg)

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
        self.__show_shutdown_screen("bro is restarting...")
        # Next launch.py run should boot straight into the app instead of standby.
        self.__request_skip_standby()
        # No projector_interface passed: projector stays on. Quitting relies on the
        # Pi launcher's bash loop (or local dev's aboutToQuit hook) to bring the app back.
        await self.__teardown(soundbar_interface=self.__soundbar_interface, quit_app=True)

    async def shutdown_app(self):
        logger.info("Shutting down app...", category="system")
        self.__show_shutdown_screen("bro is shutting down...")
        # Deliberately no request_skip_standby(): next launch.py run should enter standby.
        # Skippable via settings for dev convenience, so the projector doesn't flicker off/on every restart.
        # No config_interface wired (e.g. in tests) defaults to the original always-off behavior.
        should_turn_off_projector = self.__config_interface is None or self.__config_interface.getProjectorOffOnShutdown()
        projector_interface = self.__projector_interface if should_turn_off_projector else None
        await self.__teardown(projector_interface=projector_interface, soundbar_interface=self.__soundbar_interface, quit_app=True)

    async def reboot_device(self):
        logger.info("Rebooting device...", category="system")
        self.__show_shutdown_screen("bro is rebooting...")
        self.__request_skip_standby()
        # The shell must see this even if SIGINT interrupts Python before the app exits normally.
        self.__request_reboot_pending()
        # Stop services but don't quit yet - we still need this process alive to await the command below.
        await self.__teardown(soundbar_interface=self.__soundbar_interface, quit_app=False)

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
