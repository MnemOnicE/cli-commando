import unittest
from commando.utils.io import (
    get_category_color,
    CYAN,
    MAGENTA,
    RED,
    GREEN,
    YELLOW,
    BOLD,
)


class TestGetCategoryColor(unittest.TestCase):
    def test_cyan_categories(self):
        """Test categories that should return CYAN color"""
        self.assertEqual(get_category_color("File Management"), CYAN)
        self.assertEqual(get_category_color("Disk Utilities"), CYAN)
        self.assertEqual(get_category_color("file"), CYAN)
        self.assertEqual(get_category_color("DISK"), CYAN)

    def test_magenta_categories(self):
        """Test categories that should return MAGENTA color"""
        self.assertEqual(get_category_color("Network"), MAGENTA)
        self.assertEqual(get_category_color("Web Tools"), MAGENTA)
        self.assertEqual(get_category_color("network admin"), MAGENTA)
        self.assertEqual(get_category_color("WEB"), MAGENTA)

    def test_red_categories(self):
        """Test categories that should return RED color"""
        self.assertEqual(get_category_color("Process Management"), RED)
        self.assertEqual(get_category_color("System Utils"), RED)
        self.assertEqual(get_category_color("process"), RED)
        self.assertEqual(get_category_color("SYSTEM"), RED)

    def test_green_categories(self):
        """Test categories that should return GREEN color"""
        self.assertEqual(get_category_color("Navigation"), GREEN)
        self.assertEqual(get_category_color("Search Tools"), GREEN)
        self.assertEqual(get_category_color("navig"), GREEN)
        self.assertEqual(get_category_color("SEARCH"), GREEN)

    def test_yellow_categories(self):
        """Test categories that should return YELLOW color"""
        self.assertEqual(get_category_color("Text Editors"), YELLOW)
        self.assertEqual(get_category_color("Edit"), YELLOW)
        self.assertEqual(get_category_color("text processing"), YELLOW)
        self.assertEqual(get_category_color("EDIT"), YELLOW)

    def test_fallback_categories(self):
        """Test categories that don't match any specific keyword should return BOLD"""
        self.assertEqual(get_category_color("Unknown"), BOLD)
        self.assertEqual(get_category_color("Misc"), BOLD)
        self.assertEqual(get_category_color("Other Utilities"), BOLD)
        self.assertEqual(get_category_color(""), BOLD)


if __name__ == "__main__":
    unittest.main()
