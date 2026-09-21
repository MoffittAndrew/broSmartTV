import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py" / "interface"))

import system_interface


class FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeAsyncRunner:
    def __init__(self, result=None, raise_exc=None):
        self.result = result or FakeCompletedProcess()
        self.raise_exc = raise_exc
        self.commands = []

    async def __call__(self, command):
        self.commands.append(command)
        if self.raise_exc is not None:
            raise self.raise_exc
        return self.result


class FakeTeardown:
    def __init__(self):
        self.calls = []

    async def __call__(self, *args, **kwargs):
        self.calls.append(kwargs)


class FakeProjector:
    def __init__(self):
        self.off_calls = 0

    async def off(self):
        self.off_calls += 1


class FakeConfigInterface:
    def __init__(self, projector_off_on_shutdown=True):
        self.__projector_off_on_shutdown = projector_off_on_shutdown

    def getProjectorOffOnShutdown(self):
        return self.__projector_off_on_shutdown


def make_interface(async_command_runner=None, is_raspberry_pi=True, projector_interface=None, config_interface=None):
    teardown = FakeTeardown()
    quit_calls = []
    skip_standby_calls = []
    reboot_pending_calls = []
    shutdown_screen_calls = []
    interface = system_interface.SystemInterface(
        teardown=teardown,
        async_command_runner=async_command_runner or FakeAsyncRunner(),
        quit_app=lambda: quit_calls.append(True),
        request_skip_standby=lambda: skip_standby_calls.append(True),
        request_reboot_pending=lambda: reboot_pending_calls.append(True),
        is_raspberry_pi=is_raspberry_pi,
        projector_interface=projector_interface,
        show_shutdown_screen=lambda msg=None: shutdown_screen_calls.append(msg),
        config_interface=config_interface if config_interface is not None else FakeConfigInterface(),
    )
    return interface, teardown, quit_calls, skip_standby_calls, reboot_pending_calls, shutdown_screen_calls


@pytest.mark.asyncio
async def test_restart_app_quits_without_touching_projector():
    interface, teardown, quit_calls, skip_standby_calls, reboot_pending_calls, shutdown_screen_calls = make_interface()

    await interface.restart_app()

    assert teardown.calls == [{"soundbar_interface": None, "quit_app": True}]
    assert quit_calls == []
    assert skip_standby_calls == [True]
    assert reboot_pending_calls == []
    assert shutdown_screen_calls == ["bro is restarting..."]


@pytest.mark.asyncio
async def test_shutdown_app_shows_screen_tears_down_projector_and_skips_standby_flag():
    projector = FakeProjector()
    interface, teardown, quit_calls, skip_standby_calls, reboot_pending_calls, shutdown_screen_calls = make_interface(
        projector_interface=projector
    )

    await interface.shutdown_app()

    assert shutdown_screen_calls == ["bro is shutting down..."]
    assert teardown.calls == [{"projector_interface": projector, "soundbar_interface": None, "quit_app": True}]
    assert skip_standby_calls == []
    assert reboot_pending_calls == []


@pytest.mark.asyncio
async def test_shutdown_app_skips_projector_when_setting_disabled():
    projector = FakeProjector()
    interface, teardown, quit_calls, skip_standby_calls, reboot_pending_calls, shutdown_screen_calls = make_interface(
        projector_interface=projector, config_interface=FakeConfigInterface(projector_off_on_shutdown=False)
    )

    await interface.shutdown_app()

    assert teardown.calls == [{"projector_interface": None, "soundbar_interface": None, "quit_app": True}]


@pytest.mark.asyncio
async def test_shutdown_app_defaults_to_turning_off_projector_when_config_interface_not_wired():
    projector = FakeProjector()
    interface, teardown, quit_calls, skip_standby_calls, reboot_pending_calls, shutdown_screen_calls = make_interface(
        projector_interface=projector, config_interface=None
    )
    interface.setConfigInterface(None)

    await interface.shutdown_app()

    assert teardown.calls == [{"projector_interface": projector, "soundbar_interface": None, "quit_app": True}]


@pytest.mark.asyncio
async def test_reboot_device_runs_shutdown_command_without_projector_then_quits():
    async_runner = FakeAsyncRunner()
    interface, teardown, quit_calls, skip_standby_calls, reboot_pending_calls, shutdown_screen_calls = make_interface(
        async_command_runner=async_runner
    )

    await interface.reboot_device()

    assert teardown.calls == [{"soundbar_interface": None, "quit_app": False}]
    assert async_runner.commands == [["sudo", "shutdown", "-r", "now"]]
    assert quit_calls == [True]
    assert skip_standby_calls == [True]
    assert reboot_pending_calls == [True]
    assert shutdown_screen_calls == ["bro is rebooting..."]


@pytest.mark.asyncio
async def test_reboot_device_still_quits_when_command_fails():
    async_runner = FakeAsyncRunner(raise_exc=RuntimeError("boom"))
    interface, teardown, quit_calls, skip_standby_calls, reboot_pending_calls, shutdown_screen_calls = make_interface(
        async_command_runner=async_runner
    )

    await interface.reboot_device()

    assert teardown.calls == [{"soundbar_interface": None, "quit_app": False}]
    assert quit_calls == [True]


@pytest.mark.asyncio
async def test_reboot_device_skips_shutdown_command_on_non_raspberry_pi():
    async_runner = FakeAsyncRunner()
    interface, teardown, quit_calls, skip_standby_calls, reboot_pending_calls, shutdown_screen_calls = make_interface(
        async_command_runner=async_runner, is_raspberry_pi=False
    )

    await interface.reboot_device()

    assert async_runner.commands == []
    assert teardown.calls == [{"soundbar_interface": None, "quit_app": False}]
    assert quit_calls == [True]
