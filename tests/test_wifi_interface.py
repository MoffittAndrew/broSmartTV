import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py" / "interface"))

import wifi_interface


class FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeAsyncRunner:
    def __init__(self, result):
        self.result = result
        self.commands = []

    async def __call__(self, command):
        self.commands.append(command)
        return self.result


def make_interface(tmp_path, command_runner=None, async_command_runner=None, backend_detector=None):
    storage_path = tmp_path / "wifi.json"
    return wifi_interface.WifiInterface(
        storage_path=storage_path,
        command_runner=command_runner or (lambda *args, **kwargs: FakeCompletedProcess()),
        async_command_runner=async_command_runner or FakeAsyncRunner(FakeCompletedProcess()),
        backend_detector=backend_detector or (lambda name: name == "nmcli"),
    )


def test_save_and_load_known_networks(tmp_path):
    interface = make_interface(tmp_path)
    interface.saveKnownNetwork(wifi_interface.Network("Home WiFi", 80, "WPA2", "secret"))

    storage_path = tmp_path / "wifi.json"
    saved_payload = json.loads(storage_path.read_text(encoding="utf-8"))

    assert saved_payload["version"] == 1
    assert saved_payload["known_networks"][0]["ssid"] == "Home WiFi"
    assert saved_payload["known_networks"][0]["password"] == "secret"

    reloaded = wifi_interface.WifiInterface(
        storage_path=storage_path,
        command_runner=lambda *args, **kwargs: FakeCompletedProcess(),
        async_command_runner=FakeAsyncRunner(FakeCompletedProcess()),
    )

    known_networks = reloaded.getKnownNetworks()
    assert len(known_networks) == 1
    assert known_networks[0].ssid == "Home WiFi"
    assert known_networks[0].password == "secret"


def test_connect_requires_password_for_protected_network(tmp_path):
    interface = make_interface(tmp_path)
    protected_network = wifi_interface.Network("Cafe WiFi", 55, "WPA2")

    with pytest.raises(ValueError, match="requires a password"):
        asyncio.run(interface.connectToNetwork(protected_network))


def test_connect_uses_password_and_persists_known_network(tmp_path):
    async_runner = FakeAsyncRunner(FakeCompletedProcess())
    interface = make_interface(tmp_path, async_command_runner=async_runner)
    network = wifi_interface.Network("Cafe WiFi", 55, "WPA2")

    result = asyncio.run(interface.connectToNetwork(network, password="12345678"))

    assert result.ssid == "Cafe WiFi"
    assert async_runner.commands == [["nmcli", "device", "wifi", "connect", "Cafe WiFi", "password", "12345678"]]
    stored_networks = interface.getKnownNetworks()
    assert len(stored_networks) == 1
    assert stored_networks[0].password == "12345678"