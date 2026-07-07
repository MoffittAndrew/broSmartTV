print("Importing wifi interface...")

import asyncio
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from globals import WIFI


@dataclass
class Network:
    ssid: str
    signal_strength: int = 0
    security: str = ""
    password: str | None = None
    is_current: bool = False

    @property
    def requiresPassword(self):
        security = (self.security or "").strip().lower()
        if not security:
            return False
        return security not in {"--", "open", "none", "no", "off"}

    def to_record(self):
        return {
            "ssid": self.ssid,
            "signal_strength": self.signal_strength,
            "security": self.security,
            "password": self.password,
            "is_current": self.is_current,
        }

    @classmethod
    def from_record(cls, record):
        return cls(
            ssid=str(record.get("ssid", "")).strip(),
            signal_strength=int(record.get("signal_strength", 0) or 0),
            security=str(record.get("security", "")).strip(),
            password=record.get("password") or None,
            is_current=bool(record.get("is_current", False)),
        )


class WifiInterface:
    def __init__(self, storage_path=None, command_runner=None, async_command_runner=None, backend_detector=None, *args, **kwargs):
        self.__storage_path = Path(storage_path) if storage_path is not None else self._default_storage_path()
        self.__command_runner = command_runner or subprocess.run
        self.__async_command_runner = async_command_runner or self._run_async_command
        self.__backend_detector = backend_detector or shutil.which
        self.__known_networks = {}
        self.__current_network = None
        self.loadKnownNetworks()

    def _default_storage_path(self):
        override_path = os.getenv("BRO_SMART_TV_WIFI_STATE_PATH")
        if override_path:
            return Path(override_path)

        if os.name == "nt":
            base_dir = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        else:
            base_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))

        return base_dir / "broSmartTV" / "wifi_known_networks.json"

    def _ensure_storage_parent(self):
        self.__storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _run_command(self, command, check=False, capture_output=True, text=True):
        return self.__command_runner(
            command,
            check=check,
            capture_output=capture_output,
            text=text,
        )

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

    def _available_backends(self):
        backends = []
        if self.__backend_detector("nmcli"):
            backends.append("nmcli")
        if self.__backend_detector("iwgetid"):
            backends.append("iwgetid")
        return backends

    def _require_backend(self, required_backends):
        available = self._available_backends()
        for backend in required_backends:
            if backend in available:
                return backend
        raise RuntimeError("No supported Wi-Fi backend is available. Install NetworkManager/nmcli on the device.")

    def _parse_nmcli_wifi_line(self, line):
        parts = line.split(":", 3)
        if len(parts) < 4:
            return None

        in_use, ssid, signal_strength, security = parts
        ssid = ssid.replace(r"\:", ":").strip()
        if not ssid:
            return None

        try:
            signal_value = int(signal_strength.strip() or 0)
        except ValueError:
            signal_value = 0

        known_network = self.__known_networks.get(ssid)

        return Network(
            ssid=ssid,
            signal_strength=signal_value,
            security=security.strip(),
            password=known_network.password if known_network is not None else None,
            is_current=in_use.strip() == "*",
        )

    def _parse_nmcli_wifi_list(self, output):
        networks = []
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            network = self._parse_nmcli_wifi_line(line)
            if network is not None:
                networks.append(network)

        unique_networks = []
        seen_ssids = set()
        for network in networks:
            if network.ssid in seen_ssids:
                continue
            seen_ssids.add(network.ssid)
            unique_networks.append(network)

        unique_networks.sort(key=lambda network: (-network.signal_strength, network.ssid.lower()))
        return unique_networks

    def _sync_known_networks_from_storage(self, payload):
        known_networks = {}
        for record in payload.get("known_networks", []):
            network = Network.from_record(record)
            if network.ssid:
                known_networks[network.ssid] = network
        self.__known_networks = known_networks

    def _parse_known_networks_payload(self, payload):
        if isinstance(payload, dict):
            records = payload.get("known_networks", [])
            if isinstance(records, list):
                return records
            return []
        if isinstance(payload, list):
            return payload
        return []

    def _serialize_known_networks(self):
        return {
            "version": 1,
            "known_networks": [network.to_record() for network in self.__known_networks.values()],
        }

    def getCurrentNetwork(self):
        backend = self._require_backend(["nmcli", "iwgetid"])

        if backend == "nmcli":
            result = self._run_command([
                "nmcli",
                "-t",
                "-f",
                "IN-USE,SSID,SIGNAL,SECURITY",
                "device",
                "wifi",
                "list",
            ])
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "Failed to query current Wi-Fi network.")

            networks = self._parse_nmcli_wifi_list(result.stdout)
            for network in networks:
                if network.is_current:
                    self.__current_network = network
                    return network

            return None

        result = self._run_command(["iwgetid", "-r"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Failed to query current Wi-Fi network.")

        ssid = result.stdout.strip()
        if not ssid:
            return None

        known_network = self.__known_networks.get(ssid)
        current_network = Network(
            ssid=ssid,
            signal_strength=0,
            security=known_network.security if known_network is not None else "",
            password=known_network.password if known_network is not None else None,
        )
        self.__current_network = current_network
        return current_network

    def getAvailableNetworks(self):
        backend = self._require_backend(["nmcli"])

        if backend != "nmcli":
            raise RuntimeError("A Wi-Fi scan backend is available, but no implementation was selected.")

        result = self._run_command([
            "nmcli",
            "-t",
            "-f",
            "IN-USE,SSID,SIGNAL,SECURITY",
            "device",
            "wifi",
            "list",
            "--rescan",
            "yes",
        ])
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Failed to scan for Wi-Fi networks.")

        return self._parse_nmcli_wifi_list(result.stdout)

    async def connectToNetwork(self, network: Network, password=None):
        print(
            f"[wifi_interface] connect requested: ssid='{network.ssid if network is not None else None}', password_arg_provided={password is not None}"
        )
        if network is None or not network.ssid.strip():
            raise ValueError("A network with a valid SSID is required.")

        known_network = self.__known_networks.get(network.ssid)
        provided_password = password if password is not None else network.password
        if provided_password is None and known_network is not None:
            provided_password = known_network.password

        if network.requiresPassword and not provided_password:
            print(f"[wifi_interface] connect rejected: ssid='{network.ssid}' requires password but none available")
            raise ValueError(f"Network '{network.ssid}' requires a password.")

        backend = self._require_backend(["nmcli"])
        if backend != "nmcli":
            raise RuntimeError("A Wi-Fi connection backend is available, but no implementation was selected.")

        command = ["nmcli", "device", "wifi", "connect", network.ssid]
        if provided_password:
            command.extend(["password", provided_password])

        print(
            f"[wifi_interface] running nmcli connect: ssid='{network.ssid}', using_password={bool(provided_password)}"
        )

        result = await self.__async_command_runner(command)
        if result.stdout:
            print(f"[wifi_interface] nmcli stdout: {result.stdout.strip()}")
        if result.stderr:
            print(f"[wifi_interface] nmcli stderr: {result.stderr.strip()}")
        print(f"[wifi_interface] nmcli return code: {result.returncode}")
        if result.returncode != 0:
            error_text = (result.stderr or result.stdout or "").strip()
            error_text_lower = error_text.lower()
            if "not authorized to control networking" in error_text_lower or "not authorized" in error_text_lower:
                print(
                    "[wifi_interface] permission denied by NetworkManager. "
                    "Grant this app/user permission to manage networking (polkit/sudoers)."
                )
                raise PermissionError(
                    "Not authorized to control networking. Configure NetworkManager permissions for this app user."
                )
            raise RuntimeError(error_text or f"Failed to connect to '{network.ssid}'.")

        connected_network = Network(
            ssid=network.ssid,
            signal_strength=network.signal_strength,
            security=network.security,
            password=provided_password,
        )
        self.__current_network = connected_network
        known_network = self.__known_networks.get(connected_network.ssid)
        if known_network is None or (
            bool(connected_network.password)
            and connected_network.password != known_network.password
        ):
            self.saveKnownNetwork(connected_network)
            print(f"[wifi_interface] known network updated: ssid='{network.ssid}'")
        print(f"[wifi_interface] connect success persisted: ssid='{network.ssid}'")
        return connected_network

    def saveKnownNetwork(self, network: Network):
        if network is None or not network.ssid.strip():
            raise ValueError("A network with a valid SSID is required.")

        stored_network = Network(
            ssid=network.ssid.strip(),
            signal_strength=network.signal_strength,
            security=network.security,
            password=network.password,
        )
        self.__known_networks[stored_network.ssid] = stored_network
        self._ensure_storage_parent()
        with self.__storage_path.open("w", encoding="utf-8") as storage_file:
            json.dump(self._serialize_known_networks(), storage_file, indent=2, sort_keys=True)

    def loadKnownNetworks(self):
        source_path = self.__storage_path
        if not source_path.exists():
            self.__known_networks = {}
            return []

        try:
            with source_path.open("r", encoding="utf-8") as storage_file:
                payload = json.load(storage_file)
        except (OSError, json.JSONDecodeError):
            self.__known_networks = {}
            return []

        records = self._parse_known_networks_payload(payload)
        self._sync_known_networks_from_storage({"known_networks": records})

        # If we loaded legacy data, migrate it to the current file name.
        if source_path != self.__storage_path:
            self._ensure_storage_parent()
            with self.__storage_path.open("w", encoding="utf-8") as storage_file:
                json.dump(self._serialize_known_networks(), storage_file, indent=2, sort_keys=True)

        return list(self.__known_networks.values())

    def getKnownNetworks(self):
        return list(self.__known_networks.values())


wifiInterface = WifiInterface(storage_path=WIFI.KNOWN_NETWORKS_FILE)