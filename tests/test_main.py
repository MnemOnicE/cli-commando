import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to test the new utilities
from commando.utils.io import load_json, save_json
from commando.core.scanner import sanitize_text, suggest_command
from commando.main import StateManager

class TestCommandoUtilities(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir_path = Path(self.temp_dir.name)
        # Mock StateManager
        self.state_manager = MagicMock()
        self.state_manager.get_all_known_commands.return_value = {
            "list": {},
            "remove": {},
            "copy": {},
            "status": {}
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_json_invalid_file(self):
        """Test exception handling in load_json when an invalid file is loaded or parsing fails."""
        filepath = self.temp_dir_path / "invalid.json"

        with open(filepath, 'w') as f:
            f.write("{ invalid json content ]")

        default_val = {"default": "value"}
        result = load_json(filepath, default_val)
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
        """Test save_json to ensure that dictionary content writes successfully to a file."""
        filepath = self.temp_dir_path / "test_save.json"
        data_to_save = {"test_key": "test_value", "nested": [1, 2, 3]}

        save_json(filepath, data_to_save)
        self.assertTrue(filepath.exists())

        with open(filepath, 'r') as f:
            saved_content = json.load(f)

        self.assertEqual(saved_content, data_to_save)

    def test_suggest_command(self):
        """Test suggest_command correctly identifies close matches."""
        self.assertEqual(suggest_command("list", self.state_manager), "list")
        self.assertEqual(suggest_command("lsit", self.state_manager), "list")
        self.assertEqual(suggest_command("remov", self.state_manager), "remove")
        self.assertEqual(suggest_command("cpoy", self.state_manager), "copy")
        self.assertIsNone(suggest_command("xyz123", self.state_manager))

    def test_sanitize_text_sentinel_fix(self):
        """Test Sentinel fix: ensure ANSI escapes and control chars are stripped."""
        # ANSI Escape Code for color
        malicious = "\033[91mExploit\033[0m"
        clean = sanitize_text(malicious)
        self.assertEqual(clean, "[91mExploit[0m") # The ESC char (27) is stripped, leaving the printable parts

        # Pure unprintable
        unprintable = "Hello\x00\x01World\x07!"
        clean_unprintable = sanitize_text(unprintable)
        self.assertEqual(clean_unprintable, "HelloWorld!")

        # Valid whitespaces
        valid_whitespace = "Line 1\nLine 2\tIndented\r"
        self.assertEqual(sanitize_text(valid_whitespace), valid_whitespace)

        # Valid UTF-8
        valid_utf8 = "Привет 世界"
        self.assertEqual(sanitize_text(valid_utf8), valid_utf8)

    @patch('subprocess.run')
    def test_subprocess_mocking(self, mock_run):
        """Fortify Test Suite: Mock the subprocess.run calls to deterministically test logic."""
        mock_run.return_value = MagicMock(stdout="Mocked output", returncode=0)
        from commando.core.scanner import sanitize_text # Dummy import to ensure it works

        # We will test the analyze_strace_output from audit to ensure mocking theory works
        from commando.core.audit import analyze_strace_output
        tags = analyze_strace_output("connect(1, 2) = 0\nopenat(1, \"file\") = 3\n")
        self.assertIn("[Network Mutator]", tags)
        self.assertIn("[File Reader/Writer]", tags)

if __name__ == '__main__':
    unittest.main()
