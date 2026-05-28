import unittest
from unittest.mock import patch

from commando.utils.config import ConfigManager, DEFAULT_CONFIG

class TestConfigManagerGet(unittest.TestCase):
    def setUp(self):
        # Reset the singleton instance before each test
        ConfigManager._instance = None

        # Patch the configuration file path to prevent writing/reading actual files during simple tests
        self.patcher = patch('commando.utils.config.CONFIG_FILE')
        self.mock_config_file = self.patcher.start()

        # Mock exists to return False by default so we get DEFAULT_CONFIG
        self.mock_config_file.exists.return_value = False

        # Patch _save_internal to prevent TypeError when open() is called with a Mock path
        self.patcher_save = patch.object(ConfigManager, '_save_internal')
        self.patcher_save.start()

        # Initialize ConfigManager
        self.config_manager = ConfigManager()

    def tearDown(self):
        self.patcher.stop()
        self.patcher_save.stop()
        ConfigManager._instance = None

    def test_get_existing_key(self):
        """Test retrieving a key that exists in the config."""
        # 'auto_hook' is in DEFAULT_CONFIG
        self.assertEqual(self.config_manager.get("auto_hook"), True)

        # Manually set a key for testing
        self.config_manager.config_data["test_key"] = "test_value"
        self.assertEqual(self.config_manager.get("test_key"), "test_value")

    def test_get_missing_key_default_none(self):
        """Test retrieving a key that does not exist, expecting None as default."""
        self.assertIsNone(self.config_manager.get("non_existent_key"))

    def test_get_missing_key_custom_default(self):
        """Test retrieving a missing key with a custom default value."""
        self.assertEqual(self.config_manager.get("non_existent_key", "custom_fallback"), "custom_fallback")

if __name__ == "__main__":
    unittest.main()
import tempfile
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from commando.utils.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        # 1. Isolate the Singleton
        self.original_instance = ConfigManager._instance
        ConfigManager._instance = None

        # 2. Isolate File I/O
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mock_config_file = Path(self.temp_dir.name) / "config.json"

        # Patch the CONFIG_FILE path in the module
        self.patcher = patch("commando.utils.config.CONFIG_FILE", self.mock_config_file)
        self.patcher.start()

    def tearDown(self):
        # Restore File I/O
        self.patcher.stop()
        self.temp_dir.cleanup()

        # Restore the Singleton
        ConfigManager._instance = self.original_instance


    def test_get_existing_key(self):
        config = ConfigManager()
        config.config_data = {"test_key": "test_value"}
        self.assertEqual(config.get("test_key"), "test_value")

    def test_get_missing_key_default_none(self):
        config = ConfigManager()
        config.config_data = {"test_key": "test_value"}
        self.assertIsNone(config.get("missing_key"))

    def test_get_missing_key_custom_default(self):
        config = ConfigManager()
        config.config_data = {"test_key": "test_value"}
        self.assertEqual(config.get("missing_key", default="custom"), "custom")

    def test_get_existing_key_with_none_value(self):
        config = ConfigManager()
        config.config_data = {"test_key": None}
        self.assertIsNone(config.get("test_key", default="custom"))


    def test_get_thread_safety(self):
        """Test concurrent access to the get method."""
        config = ConfigManager()
        # Initialize with some data
        for i in range(50):
            config.set(f"key_{i}", i)

        def reader_task():
            for _ in range(100):
                # Randomly read keys, some exist, some don't
                config.get("key_25", default="fallback")
                config.get("missing_key", default="fallback")

        def writer_task():
            for i in range(50, 70):
                config.set(f"key_{i}", i)

        # Run multiple readers and writers concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 8 readers, 2 writers
            futures = []
            for _ in range(8):
                futures.append(executor.submit(reader_task))
            for _ in range(2):
                futures.append(executor.submit(writer_task))

            # Calling future.result() will propagate any exceptions with their full traceback
            for future in futures:
                future.result()
