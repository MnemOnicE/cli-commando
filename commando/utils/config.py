import threading

import yaml

from commando.utils.io import BASE_DIR

CONFIG_FILE = BASE_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "allowed_paths": [
        "/data/data/com.termux/files/usr/bin",
        "/system/bin",
        "/bin",
        "/usr/bin",
    ],
    "auto_hook": True,
    "trusted_binaries": [],
    "blacklisted_binaries": [],
}


class ConfigManager:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                # Initialize variables before _load
                cls._instance.config_data = {}
                cls._instance._load()
            return cls._instance

    def _load(self):
        with self._lock:
            if not CONFIG_FILE.exists():
                self.config_data = DEFAULT_CONFIG.copy()
                self._save_internal()
            else:
                try:
                    with open(CONFIG_FILE, "r") as f:
                        loaded = yaml.safe_load(f)
                        if loaded and isinstance(loaded, dict):
                            # Merge defaults for missing keys
                            self.config_data = DEFAULT_CONFIG.copy()
                            self.config_data.update(loaded)
                        else:
                            self.config_data = DEFAULT_CONFIG.copy()
                except Exception:
                    self.config_data = DEFAULT_CONFIG.copy()

    def _save_internal(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                yaml.dump(self.config_data, f, default_flow_style=False)
        except Exception:
            pass

    def get(self, key, default=None):
        with self._lock:
            return self.config_data.get(key, default)

    def set(self, key, value):
        with self._lock:
            self.config_data[key] = value
            self._save_internal()
