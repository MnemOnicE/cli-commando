import unittest
import tempfile
import json
import os
from pathlib import Path
from commando.main import load_json, save_json, suggest_command

class TestCommandoUtilities(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_json_invalid_file(self):
        """Test exception handling in load_json when an invalid file is loaded or parsing fails."""
        filepath = self.temp_dir_path / "invalid.json"

        # Create an invalid JSON file
        with open(filepath, 'w') as f:
            f.write("{ invalid json content ]")

        default_val = {"default": "value"}

        # Test loading the invalid file
        result = load_json(filepath, default_val)

        # Verify it falls back to the default value
        self.assertEqual(result, default_val)

    def test_load_json_valid_file(self):
        """Test load_json with a valid file to ensure it works correctly when not failing."""
        filepath = self.temp_dir_path / "valid.json"
        valid_data = {"key": "value"}

        with open(filepath, 'w') as f:
            json.dump(valid_data, f)

        result = load_json(filepath, {"default": "value"})
        self.assertEqual(result, valid_data)

    def test_load_json_nonexistent_file(self):
        """Test load_json with a nonexistent file."""
        filepath = self.temp_dir_path / "nonexistent.json"
        default_val = {"default": "value"}

        result = load_json(filepath, default_val)
        self.assertEqual(result, default_val)

    def test_save_json(self):
        """No tests exist for save_json to ensure that dictionary content writes successfully to a file."""
        filepath = self.temp_dir_path / "test_save.json"
        data_to_save = {"test_key": "test_value", "nested": [1, 2, 3]}

        # Call save_json
        save_json(filepath, data_to_save)

        # Verify file exists
        self.assertTrue(filepath.exists())

        # Read the file directly to verify content
        with open(filepath, 'r') as f:
            saved_content = json.load(f)

        # Verify the content matches what we saved
        self.assertEqual(saved_content, data_to_save)

    def test_suggest_command(self):
    def test_suggest_command(self):
        """Test suggest_command to verify logic identifying close matches using difflib."""
        # Using a context manager or patching get_all_known_commands might be necessary
        # Let's import mock to patch get_all_known_commands
        from unittest.mock import patch

        known_commands = {
            "list": {},
            "remove": {},
            "copy": {},
            "status": {}
        }

        with patch('commando.main.get_all_known_commands', return_value=known_commands):
            # Test exact match (not strictly needed since we normally wouldn't call suggest on exact match, but good to check)
            self.assertEqual(suggest_command("list"), "list")

            # Test close matches (typos)
            self.assertEqual(suggest_command("lsit"), "list")
            self.assertEqual(suggest_command("remov"), "remove")
            self.assertEqual(suggest_command("cpoy"), "copy")

            # Test complete mismatch
            self.assertIsNone(suggest_command("xyz123"))

if __name__ == '__main__':
    unittest.main()
