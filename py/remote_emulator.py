#!/usr/bin/env python3
"""Standalone BLE remote emulator for the bro Smart TV project.

This script advertises itself as the "bro-ito" BLE remote and forwards
keyboard presses to the TV-side remote_interface implementation.
It is intended to run on a laptop/desktop machine with Windows BLE support.
"""

import argparse
import asyncio
import os
import sys
import uuid
from typing import Optional

# Allow importing the shared project globals.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from globals import INPUT, REMOTE

try:
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows environments
    msvcrt = None

try:
    import winrt.windows.devices.bluetooth.advertisement as bluetooth_advertisement
    import winrt.windows.devices.bluetooth.genericattributeprofile as genericattributeprofile
    from winrt.windows.storage.streams import DataWriter
except ImportError as exc:  # pragma: no cover - environment-specific
    raise SystemExit(
        "This emulator requires Windows BLE support. Install the winrt package and run it on Windows."
    ) from exc


SERVICE_UUID = uuid.UUID(REMOTE.SERVICE_UUID)
CHARACTERISTIC_UUID = uuid.UUID(REMOTE.CHARACTERISTIC_UUID)
REMOTE_NAME = REMOTE.NAME

# Map keyboard input to the same logical button names used by the TV-side input handling.
# The existing GUI keyboard mapping is preserved where possible, and extra buttons are added.
KEYMAP = {
    "q": INPUT.POWER,
    " ": INPUT.HOME,
    "\r": INPUT.SELECT,
    "\t": INPUT.MENU,
    "\x1b": INPUT.RETURN,
    "up": INPUT.NAV_UP,
    "down": INPUT.NAV_DOWN,
    "left": INPUT.NAV_LEFT,
    "right": INPUT.NAV_RIGHT,
    "pageup": INPUT.VOL_UP,
    "pagedown": INPUT.VOL_DOWN,
    "f1": INPUT.MIC,
}


def build_advertisement_payload(name: str):
    """Create a BLE advertisement payload with the remote name."""
    writer = DataWriter()
    writer.write_bytes(name.encode("utf-8"))
    buffer = writer.detach_buffer()

    section = bluetooth_advertisement.BluetoothLEAdvertisementDataSection(
        0x09,
        buffer,
    )
    advertisement = bluetooth_advertisement.BluetoothLEAdvertisement()
    advertisement.data_sections.append(section)
    return advertisement


async def send_signal(characteristic, signal: str) -> None:
    """Send a string payload to the connected TV as a notification."""
    writer = DataWriter()
    writer.write_bytes(signal.encode("utf-8"))
    await characteristic.notify_value_async(writer.detach_buffer())


def read_console_key() -> Optional[str]:
    """Read a single keypress from the console without requiring Enter."""
    if msvcrt is None:
        return None

    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        ext = msvcrt.getwch()
        mapping = {
            "H": "up",
            "P": "down",
            "K": "left",
            "M": "right",
            "I": "pageup",
            "Q": "pagedown",
        }
        return mapping.get(ext)

    if key == "\r":
        return "\r"
    if key == "\t":
        return "\t"
    if key == "\x1b":
        return "\x1b"
    if key == " ":
        return " "
    return key.lower() if len(key) == 1 else None


async def keyboard_loop(characteristic) -> None:
    """Forward keypresses into Bluetooth notifications."""
    print("Remote emulator ready. Press keys to send them to the TV.")
    print("Mappings: q=POWER, space=HOME, enter=SELECT, tab=MENU, escape=RETURN")
    print("Arrows=nav, PageUp/PageDown=vol, F1=MIC")
    print("Press Ctrl+C to quit.\n")

    while True:
        key_name = await asyncio.to_thread(read_console_key)
        if key_name is None:
            continue

        if key_name not in KEYMAP:
            continue

        signal = KEYMAP[key_name]
        print(f"Sending {signal}...")
        await send_signal(characteristic, signal)
        await send_signal(characteristic, f"RELEASED_{signal}")


async def main(dry_run: bool = False) -> None:
    if msvcrt is None:
        raise SystemExit("This script only works on Windows because it uses msvcrt.")

    print(f"Creating Bluetooth remote emulator for {REMOTE_NAME}...")

    if dry_run:
        print("Dry run complete. Bluetooth advertising was not started.")
        return

    provider_result = await genericattributeprofile.GattServiceProvider.create_async(SERVICE_UUID)
    provider = provider_result.service_provider
    service = provider.service

    characteristic_params = genericattributeprofile.GattLocalCharacteristicParameters()
    characteristic_params.characteristic_properties = (
        genericattributeprofile.GattCharacteristicProperties.NOTIFY
        | genericattributeprofile.GattCharacteristicProperties.READ
    )
    characteristic_params.read_protection_level = 0
    characteristic_params.write_protection_level = 0

    characteristic = await service.create_characteristic_async(
        CHARACTERISTIC_UUID,
        characteristic_params,
    )

    advertisement = build_advertisement_payload(REMOTE_NAME)
    publisher = bluetooth_advertisement.BluetoothLEAdvertisementPublisher(advertisement)
    try:
        publisher.start()
    except PermissionError as exc:
        raise SystemExit(
            "Bluetooth advertisement access was denied by Windows. "
            "Run the script in an elevated terminal or enable Bluetooth permissions and try again."
        ) from exc

    advertising_params = genericattributeprofile.GattServiceProviderAdvertisingParameters()
    advertising_params.is_connectable = True
    advertising_params.is_discoverable = True
    provider.start_advertising(advertising_params)

    print("Advertising remote. Waiting for the TV to connect...")

    try:
        await asyncio.create_task(keyboard_loop(characteristic))
    except KeyboardInterrupt:
        print("Stopping remote emulator...")
    finally:
        publisher.stop()
        provider.stop_advertising()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emulate the bro-ito BLE remote from a laptop")
    parser.add_argument("--dry-run", action="store_true", help="Validate imports and exit without advertising")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
