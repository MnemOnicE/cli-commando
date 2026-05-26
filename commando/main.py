import argparse
import sys

from commando.core import audit, scanner
from commando.ui import dashboard

# Import separated modules
from commando.utils.io import (
    BLACKLIST_FILE,
    CUSTOM_DICT_FILE,
    HISTORY_FILE,
    PENDING_DICT_FILE,
    load_json,
    save_json,
)

BEGINNER_GUIDE = {
    "mkdir": {
        "desc": "Creates a new directory (folder).",
        "example": "mkdir -p parent/child/folder",
        "category": "File Management",
    },
    "ls": {
        "desc": "Lists the files and folders in your current directory.",
        "example": "ls -lahS",
        "category": "File Management",
    },
    "rm": {
        "desc": "Removes (deletes) files or directories. Be careful!",
        "example": "rm -rf tmp_dir/",
        "category": "File Management",
    },
    "cp": {
        "desc": "Copies files or directories.",
        "example": "cp -r source_dir/ backup_dir/",
        "category": "File Management",
    },
    "cd": {
        "desc": "Changes your current directory.",
        "example": "cd -",
        "category": "Navigation",
    },
    "pwd": {
        "desc": "Print Working Directory. Tells you where you are.",
        "example": "pwd -P",
        "category": "Navigation",
    },
    "echo": {
        "desc": "Prints text to the terminal screen.",
        "example": "echo 'export PATH=$PATH:~/bin' >> ~/.bashrc",
        "category": "Text Processing",
    },
    "cat": {
        "desc": "Reads a file and outputs its contents to the screen.",
        "example": "cat -n my_script.py",
        "category": "Text Processing",
    },
    "grep": {
        "desc": "Searches for a specific pattern of text inside files.",
        "example": "grep -ri 'TODO' ./src",
        "category": "Text Processing",
    },
    "clear": {
        "desc": "Clears the terminal screen.",
        "example": "clear && echo 'Terminal refreshed.'",
        "category": "System",
    },
    "help": {
        "desc": "Displays info about built-in bash commands.",
        "example": "help cd | less",
        "category": "System",
    },
    "chmod": {
        "desc": "Changes read/write/execute permissions.",
        "example": "chmod +x *.sh",
        "category": "System",
    },
}


class StateManager:
    def __init__(self):
        self.session_history = load_json(HISTORY_FILE, {})
        if isinstance(self.session_history, list):
            self.session_history = {cmd: 0 for cmd in self.session_history}
        self.custom_guide = load_json(CUSTOM_DICT_FILE, {})
        self.probe_blacklist = load_json(BLACKLIST_FILE, [])
        self.pending_imports = load_json(PENDING_DICT_FILE, {})

    def get_all_known_commands(self):
        return {**BEGINNER_GUIDE, **self.custom_guide}

    def get_history(self):
        return self.session_history

    def get_pending(self):
        return self.pending_imports

    def save_history(self):
        save_json(HISTORY_FILE, self.session_history)

    def save_custom(self):
        save_json(CUSTOM_DICT_FILE, self.custom_guide)

    def save_blacklist(self):
        save_json(BLACKLIST_FILE, self.probe_blacklist)

    def save_pending(self):
        save_json(PENDING_DICT_FILE, self.pending_imports)


def cli():
    parser = argparse.ArgumentParser(description="cli-commando")
    parser.add_argument("command", nargs="*", help="Command to search for or execute")
    parser.add_argument(
        "--json", action="store_true", help="Output in JSON format (headless mode)"
    )
    parser.add_argument(
        "--audit", action="store_true", help="Run kinetic audit using strace"
    )
    parser.add_argument(
        "--generate-completion",
        action="store_true",
        help="Generate bash completion script",
    )
    parser.add_argument("--complete", type=str, help=argparse.SUPPRESS)

    args = parser.parse_args()

    state_manager = StateManager()

    if args.generate_completion:
        print(
            """_commando_completions() {
    local curr_arg=${COMP_WORDS[COMP_CWORD]}
    COMPREPLY=( $(commando --complete "$curr_arg") )
}
complete -F _commando_completions commando"""
        )
        sys.exit(0)

    if args.complete is not None:
        prefix = args.complete.lower()
        known = state_manager.get_all_known_commands()
        matches = [cmd for cmd in known.keys() if cmd.lower().startswith(prefix)]
        print(" ".join(matches))
        sys.exit(0)

    headless = args.json
    audit_mode = args.audit
    command_args = args.command

    if command_args and command_args[0] == "search":
        command_args.pop(0)

    def search_wrapper(cmd):
        audit.search_command(cmd, state_manager, scanner, headless, audit_mode)

    if command_args:
        search_wrapper(" ".join(command_args))
    else:
        dashboard.main_loop(state_manager, search_wrapper, scanner.auto_scan_system)


if __name__ == "__main__":
    cli()
