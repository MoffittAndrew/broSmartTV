import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py" / "interface"))

import config_interface


DEFAULTS = {"projector_off_on_shutdown": True}


def test_defaults_used_when_no_file_exists(tmp_path):
    interface = config_interface.ConfigInterface(storage_path=tmp_path / "config.json", defaults=DEFAULTS)

    assert interface.getProjectorOffOnShutdown() is True


def test_set_persists_to_disk(tmp_path):
    storage_path = tmp_path / "config.json"
    interface = config_interface.ConfigInterface(storage_path=storage_path, defaults=DEFAULTS)

    interface.setProjectorOffOnShutdown(False)

    saved_payload = json.loads(storage_path.read_text(encoding="utf-8"))
    assert saved_payload["version"] == 1
    assert saved_payload["settings"]["projector_off_on_shutdown"] is False


def test_reload_picks_up_saved_value(tmp_path):
    storage_path = tmp_path / "config.json"
    interface = config_interface.ConfigInterface(storage_path=storage_path, defaults=DEFAULTS)
    interface.setProjectorOffOnShutdown(False)

    reloaded = config_interface.ConfigInterface(storage_path=storage_path, defaults=DEFAULTS)

    assert reloaded.getProjectorOffOnShutdown() is False


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    storage_path = tmp_path / "config.json"
    storage_path.write_text("not valid json", encoding="utf-8")

    interface = config_interface.ConfigInterface(storage_path=storage_path, defaults=DEFAULTS)

    assert interface.getProjectorOffOnShutdown() is True


def test_unknown_keys_in_file_are_ignored(tmp_path):
    storage_path = tmp_path / "config.json"
    storage_path.write_text(
        json.dumps({"version": 1, "settings": {"projector_off_on_shutdown": False, "some_removed_setting": "x"}}),
        encoding="utf-8",
    )

    interface = config_interface.ConfigInterface(storage_path=storage_path, defaults=DEFAULTS)

    assert interface.getProjectorOffOnShutdown() is False
    assert interface.get("some_removed_setting") is None
