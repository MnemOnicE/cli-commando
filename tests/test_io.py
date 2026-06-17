import unittest
import commando.utils.io as io


class TestGetCategoryColor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Save original colors to restore them later
        cls.original_colors = {
            "CYAN": io.CYAN,
            "MAGENTA": io.MAGENTA,
            "RED": io.RED,
            "GREEN": io.GREEN,
            "YELLOW": io.YELLOW,
            "BOLD": io.BOLD,
        }
        # Set distinct mock values to prevent false positives in non-TTY/CI environments
        io.CYAN = "mock_cyan"
        io.MAGENTA = "mock_magenta"
        io.RED = "mock_red"
        io.GREEN = "mock_green"
        io.YELLOW = "mock_yellow"
        io.BOLD = "mock_bold"

    @classmethod
    def tearDownClass(cls):
        # Restore original colors
        io.CYAN = cls.original_colors["CYAN"]
        io.MAGENTA = cls.original_colors["MAGENTA"]
        io.RED = cls.original_colors["RED"]
        io.GREEN = cls.original_colors["GREEN"]
        io.YELLOW = cls.original_colors["YELLOW"]
        io.BOLD = cls.original_colors["BOLD"]

    def test_cyan_categories(self):
        """Test categories that should return CYAN color"""
        self.assertEqual(io.get_category_color("File Management"), io.CYAN)
        self.assertEqual(io.get_category_color("Disk Utilities"), io.CYAN)
        self.assertEqual(io.get_category_color("file"), io.CYAN)
        self.assertEqual(io.get_category_color("DISK"), io.CYAN)

    def test_magenta_categories(self):
        """Test categories that should return MAGENTA color"""
        self.assertEqual(io.get_category_color("Network"), io.MAGENTA)
        self.assertEqual(io.get_category_color("Web Tools"), io.MAGENTA)
        self.assertEqual(io.get_category_color("network admin"), io.MAGENTA)
        self.assertEqual(io.get_category_color("WEB"), io.MAGENTA)

    def test_red_categories(self):
        """Test categories that should return RED color"""
        self.assertEqual(io.get_category_color("Process Management"), io.RED)
        self.assertEqual(io.get_category_color("System Utils"), io.RED)
        self.assertEqual(io.get_category_color("process"), io.RED)
        self.assertEqual(io.get_category_color("SYSTEM"), io.RED)

    def test_green_categories(self):
        """Test categories that should return GREEN color"""
        self.assertEqual(io.get_category_color("Navigation"), io.GREEN)
        self.assertEqual(io.get_category_color("Search Tools"), io.GREEN)
        self.assertEqual(io.get_category_color("navig"), io.GREEN)
        self.assertEqual(io.get_category_color("SEARCH"), io.GREEN)

    def test_yellow_categories(self):
        """Test categories that should return YELLOW color"""
        self.assertEqual(io.get_category_color("Text Editors"), io.YELLOW)
        self.assertEqual(io.get_category_color("Edit"), io.YELLOW)
        self.assertEqual(io.get_category_color("Text Management"), io.YELLOW)
        self.assertEqual(io.get_category_color("EDIT"), io.YELLOW)

    def test_fallback_categories(self):
        """Test categories that don't match any specific keyword should return BOLD"""
        self.assertEqual(io.get_category_color("Unknown"), io.BOLD)
        self.assertEqual(io.get_category_color("Misc"), io.BOLD)
        self.assertEqual(io.get_category_color("Other Utilities"), io.BOLD)
        self.assertEqual(io.get_category_color(""), io.BOLD)


if __name__ == "__main__":
    unittest.main()
