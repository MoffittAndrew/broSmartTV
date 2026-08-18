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


def make_interface(async_command_runner=None):
    teardown = FakeTeardown()
    quit_calls = []
    interface = system_interface.SystemInterface(
        teardown=teardown,
        async_command_runner=async_command_runner or FakeAsyncRunner(),
        quit_app=lambda: quit_calls.append(True),
    )
    return interface, teardown, quit_calls


@pytest.mark.asyncio
async def test_restart_app_quits_without_touching_projector():
    interface, teardown, quit_calls = make_interface()

    await interface.restart_app()

    assert teardown.calls == [{"quit_app": True}]
    assert quit_calls == []


@pytest.mark.asyncio
async def test_reboot_device_runs_shutdown_command_without_projector_then_quits():
    async_runner = FakeAsyncRunner()
    interface, teardown, quit_calls = make_interface(async_command_runner=async_runner)

    await interface.reboot_device()

    assert teardown.calls == [{"quit_app": False}]
    assert async_runner.commands == [["sudo", "shutdown", "-r", "now"]]
    assert quit_calls == [True]


@pytest.mark.asyncio
async def test_reboot_device_still_quits_when_command_fails():
    async_runner = FakeAsyncRunner(raise_exc=RuntimeError("boom"))
    interface, teardown, quit_calls = make_interface(async_command_runner=async_runner)

    await interface.reboot_device()

    assert teardown.calls == [{"quit_app": False}]
    assert quit_calls == [True]
