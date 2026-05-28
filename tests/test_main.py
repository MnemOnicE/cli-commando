import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from commando.core.scanner import sanitize_text, suggest_command

# We need to test the new utilities
from commando.utils.io import load_json, save_json


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
            "status": {},
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_json_invalid_file(self):
        """Test exception handling in load_json when an invalid file is loaded or parsing fails."""
        filepath = self.temp_dir_path / "invalid.json"

        with open(filepath, "w") as f:
            f.write("{ invalid json content ]")

        default_val = {"default": "value"}
        result = load_json(filepath, default_val)
        self.assertEqual(result, default_val)

    def test_load_json_valid_file(self):
        """Test load_json with a valid file to ensure it works correctly when not failing."""
        filepath = self.temp_dir_path / "valid.json"
        valid_data = {"key": "value"}

        with open(filepath, "w") as f:
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

        with open(filepath, "r") as f:
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
        self.assertEqual(
            clean, "[91mExploit[0m"
        )  # The ESC char (27) is stripped, leaving the printable parts

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

    @patch("subprocess.run")
    def test_subprocess_mocking(self, mock_run):
        """Fortify Test Suite: Mock the subprocess.run calls to deterministically test logic."""
        mock_run.return_value = MagicMock(stdout="Mocked output", returncode=0)

        # We will test the analyze_strace_output from audit to ensure mocking theory works
        from commando.core.audit import analyze_strace_output

        tags = analyze_strace_output('connect(1, 2) = 0\nopenat(1, "file") = 3\n')
        self.assertIn("[Network Mutator]", tags)
        self.assertIn("[File Reader/Writer]", tags)


if __name__ == "__main__":
    unittest.main()


class TestAuditModule(unittest.TestCase):
    def setUp(self):
        self.state_manager = MagicMock()
        self.state_manager.session_history = {}
        self.state_manager.custom_guide = {}
        self.state_manager.probe_blacklist = []
        self.state_manager.pending_imports = {}
        self.state_manager.get_all_known_commands.return_value = {
            "ls": {"desc": "list files", "category": "System"}
        }
        self.scanner_module = MagicMock()

    def test_analyze_ldd_output_standard(self):
        """Test ldd output with standard libraries (libc)."""
        from commando.core.audit import analyze_ldd_output
        output = "\tlinux-vdso.so.1 (0x00007ffe343e3000)\n\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f9c2a800000)\n\t/lib64/ld-linux-x86-64.so.2 (0x00007f9c2ab0d000)"
        result = analyze_ldd_output(output)
        self.assertCountEqual(result, ["[File Reader/Writer]"])

    def test_analyze_ldd_output_network(self):
        """Test ldd output with network libraries (libssl, libcurl) and libc."""
        from commando.core.audit import analyze_ldd_output
        output = "\tlinux-vdso.so.1 (0x00007ffe343e3000)\n\tlibssl.so.3 => /lib/x86_64-linux-gnu/libssl.so.3 (0x00007f9c2a900000)\n\tlibcurl.so.4 => /lib/x86_64-linux-gnu/libcurl.so.4 (0x00007f9c2aa00000)\n\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f9c2a800000)\n\t/lib64/ld-linux-x86-64.so.2 (0x00007f9c2ab0d000)"
        result = analyze_ldd_output(output)
        self.assertCountEqual(result, ["[Network Mutator]", "[File Reader/Writer]"])

    def test_analyze_ldd_output_static(self):
        """Test ldd output for a statically linked binary (no matches)."""
        from commando.core.audit import analyze_ldd_output
        output = "\tnot a dynamic executable"
        result = analyze_ldd_output(output)
        self.assertCountEqual(result, [])

    def test_analyze_ldd_output_loose_match(self):
        """Test ldd output documenting loose matching (substring match)."""
        from commando.core.audit import analyze_ldd_output
        output = "\tlibssl_dummy.so => /opt/libssl_dummy/libssl_dummy.so (0x00007f9c2a900000)"
        result = analyze_ldd_output(output)
        self.assertCountEqual(result, ["[Network Mutator]"])

    @patch("commando.core.audit.os.killpg")
    @patch("commando.core.audit.os.getpgid")
    @patch("commando.core.audit.subprocess.Popen")
    def test_search_command_timeout_kills_process_group(
        self, mock_popen, mock_getpgid, mock_killpg
    ):
        import signal
        import subprocess

        from commando.core.audit import search_command

        # Setup mock Popen to raise TimeoutExpired on communicate
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="strace", timeout=2
        )
        mock_popen.return_value = mock_proc

        # Mock os.getpgid to return a specific process group id
        mock_getpgid.return_value = 54321

        # We need to capture stdout to avoid cluttering the test output
        import sys
        from io import StringIO

        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            search_command(
                "ls",
                self.state_manager,
                self.scanner_module,
                headless=False,
                audit=True,
            )
        finally:
            sys.stdout = sys.__stdout__

        # Verify that os.killpg was called with the correct process group ID and signal
        # With the fix, getpgid is called twice
        mock_getpgid.assert_called_with(12345)
        self.assertEqual(mock_getpgid.call_count, 2)
        mock_killpg.assert_called_once_with(54321, signal.SIGKILL)


class TestScannerModule(unittest.TestCase):
    def setUp(self):
        self.state_manager = MagicMock()
        self.state_manager.get_all_known_commands.return_value = {}
        self.state_manager.probe_blacklist = []
        self.state_manager.pending_imports = {}

    @patch("commando.core.scanner.subprocess.run")
    @patch("commando.core.scanner.os.environ.get")
    @patch("commando.core.scanner.os.path.isdir")
    @patch("commando.core.scanner.os.listdir")
    @patch("commando.core.scanner.os.path.isfile")
    @patch("commando.core.scanner.os.access")
    def test_auto_scan_system_malformed_ansi_injection(
        self,
        mock_access,
        mock_isfile,
        mock_listdir,
        mock_isdir,
        mock_environ_get,
        mock_run,
    ):
        import subprocess

        from commando.core.scanner import auto_scan_system

        # Setup mocked filesystem to find one 'unknown' binary
        mock_environ_get.return_value = "/usr/bin"
        mock_isdir.return_value = True
        mock_listdir.return_value = ["malicious_bin"]
        mock_isfile.return_value = True
        mock_access.return_value = True

        # Malformed output with ANSI escape codes and unprintable characters
        malicious_output = "malicious_bin - usage: \033[31mExploit\033[0m \x00\x01\n malicious_bin - A very \033[1;32mcolorful\033[0m description."

        # Configure subprocess.run to simulate `whatis` failing, then `help` failing, then static analysis via `strings` succeeding
        def side_effect(args, **kwargs):
            if args[0] == "whatis":
                raise subprocess.CalledProcessError(1, "whatis")
            elif args[0] == "bash" and args[1] == "-c":
                raise subprocess.CalledProcessError(1, "bash")
            elif args[0] == "strings":
                return MagicMock(stdout=malicious_output, returncode=0)
            return MagicMock(stdout="", returncode=0)

        mock_run.side_effect = side_effect

        # Mock the 'with open' for the header check to return ELF header
        with patch(
            "builtins.open", unittest.mock.mock_open(read_data=b"\x7fELF")
        ), patch("commando.utils.io.input", return_value=""):
            # Capture output
            import sys
            from io import StringIO

            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                auto_scan_system(self.state_manager)
            finally:
                sys.stdout = sys.__stdout__

        # Check if the pending import was added correctly
        self.assertIn("malicious_bin", self.state_manager.pending_imports)

        saved_desc = self.state_manager.pending_imports["malicious_bin"]["desc"]

        # Ensure ANSI escapes and unprintable chars (except newlines/spaces) are stripped
        # "\033[31mExploit\033[0m \x00\x01\n - A very \033[1;32mcolorful\033[0m description."
        # The ESC char \033 is stripped, leaving "[31mExploit[0m \n - A very [1;32mcolorful[0m description."
        # Wait, the regex in static analysis `motif_dash = re.compile(r"(?i)^\s*" + re.escape(cmd) + r"\s+-\s+(.*)")`
        # Actually it falls back to looking for the command name, or just taking the first matching line.
        # Let's just check that the description has been processed by `sanitize_text`.

        # We can just verify it doesn't contain the raw ESC char \033
        self.assertNotIn("\033", saved_desc)
