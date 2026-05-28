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

        # Mock with_suffix so _save_internal doesn't fail trying to create temp_file
        self.mock_config_file.with_suffix.return_value.replace.return_value = None

        # Initialize ConfigManager
        self.config_manager = ConfigManager()

    def tearDown(self):
        self.patcher.stop()
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
