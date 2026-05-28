import unittest
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
        for i in range(100):
            config.set(f"key_{i}", i)

        errors = []

        def reader_task():
            try:
                for _ in range(1000):
                    # Randomly read keys, some exist, some don't
                    config.get("key_50", default="fallback")
                    config.get("missing_key", default="fallback")
            except Exception as e:
                errors.append(e)

        def writer_task():
            try:
                for i in range(100, 200):
                    config.set(f"key_{i}", i)
            except Exception as e:
                errors.append(e)

        # Run multiple readers and writers concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 8 readers, 2 writers
            futures = []
            for _ in range(8):
                futures.append(executor.submit(reader_task))
            for _ in range(2):
                futures.append(executor.submit(writer_task))

            for future in futures:
                future.result()

        self.assertEqual(len(errors), 0, f"Thread safety errors occurred: {errors}")
