import sys
import os
import json
from datetime import datetime
from pathlib import Path

# ANSI Escape Codes
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
MAGENTA = '\033[95m'
BOLD = '\033[1m'
RESET = '\033[0m'

if sys.stdout is None or not sys.stdout.isatty() or os.environ.get('NO_COLOR'):
    CYAN = ''
    GREEN = ''
    YELLOW = ''
    RED = ''
    MAGENTA = ''
    BOLD = ''
    RESET = ''

BASE_DIR = Path.home() / ".commando"
BASE_DIR.mkdir(exist_ok=True)

HISTORY_FILE = BASE_DIR / "history.json"
CUSTOM_DICT_FILE = BASE_DIR / "custom.json"
BLACKLIST_FILE = BASE_DIR / "blacklist.json"
PENDING_DICT_FILE = BASE_DIR / "pending.json"
DEBUG_LOG_FILE = BASE_DIR / "debug.log"

def load_json(filepath, default_val):
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            pass
    return default_val

def save_json(filepath, data):
    temp_path = filepath.with_suffix('.json.tmp')
    with open(temp_path, 'w') as f:
        json.dump(data, f, indent=4)
    os.replace(temp_path, filepath)

def write_log(cmd, reason, raw_output=""):
    """Writes failed probes to the debug log."""
    if DEBUG_LOG_FILE.exists() and DEBUG_LOG_FILE.stat().st_size > 1048576:
        try:
            DEBUG_LOG_FILE.replace(DEBUG_LOG_FILE.with_suffix('.log.1'))
        except Exception:
            pass

    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(DEBUG_LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {cmd} | {reason}\n")
        if raw_output:
            clean_out = raw_output.strip()[:150].replace('\n', ' ')
            f.write(f"    -> RAW: {clean_out}...\n")

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def pause():
    try:
        input(f"\n{YELLOW}Press Enter to continue...{RESET}")
    except (EOFError, KeyboardInterrupt):
        print()
