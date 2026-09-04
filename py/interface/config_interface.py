from app_logging import get_adapter

logger = get_adapter("config", "config")
logger.info("Importing config interface...")

import json
from pathlib import Path

from globals import CONFIG


class ConfigInterface:
    """Generic persisted key/value settings store; add new settings via CONFIG.DEFAULTS."""

    def __init__(self, storage_path=None, defaults=None, *args, **kwargs):
        self.__storage_path = Path(storage_path) if storage_path is not None else Path(CONFIG.STORAGE_FILE)
        self.__defaults = dict(defaults) if defaults is not None else dict(CONFIG.DEFAULTS)
        self.__values = dict(self.__defaults)
        self.loadConfig()

    def loadConfig(self):
        if not self.__storage_path.exists():
            self.__values = dict(self.__defaults)
            return

        try:
            with self.__storage_path.open("r", encoding="utf-8") as storage_file:
                payload = json.load(storage_file)
        except (OSError, json.JSONDecodeError) as exc:
            logger.exception("Failed to load config, using defaults", exc, component="config")
            self.__values = dict(self.__defaults)
            return

        settings = payload.get("settings", {}) if isinstance(payload, dict) else {}
        # Only known keys are honored, so removed settings in old files can't resurface.
        self.__values = {key: settings.get(key, default) for key, default in self.__defaults.items()}

    def _save(self):
        self.__storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "settings": self.__values}
        with self.__storage_path.open("w", encoding="utf-8") as storage_file:
            json.dump(payload, storage_file, indent=2, sort_keys=True)

    def get(self, key):
        return self.__values.get(key, self.__defaults.get(key))

    def set(self, key, value):
        self.__values[key] = value
        self._save()

    def getProjectorOffOnShutdown(self):
        return self.get("projector_off_on_shutdown")

    def setProjectorOffOnShutdown(self, value):
        self.set("projector_off_on_shutdown", value)


configInterface = ConfigInterface()
