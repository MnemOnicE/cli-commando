import subprocess
import shutil
import random
import sys
import os
import json
import difflib
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

BASE_DIR = Path.home() / ".bashlearn"
BASE_DIR.mkdir(exist_ok=True)

HISTORY_FILE = BASE_DIR / "history.json"
CUSTOM_DICT_FILE = BASE_DIR / "custom.json"
BLACKLIST_FILE = BASE_DIR / "blacklist.json"
DEBUG_LOG_FILE = BASE_DIR / "debug.log"

BEGINNER_GUIDE = {
    "mkdir": {"desc": "Creates a new directory (folder).", "example": "mkdir -p parent/child/folder", "category": "File Management"},
    "ls": {"desc": "Lists the files and folders in your current directory.", "example": "ls -lahS", "category": "File Management"},
    "rm": {"desc": "Removes (deletes) files or directories. Be careful!", "example": "rm -rf tmp_dir/", "category": "File Management"},
    "cp": {"desc": "Copies files or directories.", "example": "cp -r source_dir/ backup_dir/", "category": "File Management"},
    "cd": {"desc": "Changes your current directory.", "example": "cd -", "category": "Navigation"},
    "pwd": {"desc": "Print Working Directory. Tells you where you are.", "example": "pwd -P", "category": "Navigation"},
    "echo": {"desc": "Prints text to the terminal screen.", "example": "echo 'export PATH=$PATH:~/bin' >> ~/.bashrc", "category": "Text Processing"},
    "cat": {"desc": "Reads a file and outputs its contents to the screen.", "example": "cat -n my_script.py", "category": "Text Processing"},
    "grep": {"desc": "Searches for a specific pattern of text inside files.", "example": "grep -ri 'TODO' ./src", "category": "Text Processing"},
    "clear": {"desc": "Clears the terminal screen.", "example": "clear && echo 'Terminal refreshed.'", "category": "System"},
    "help": {"desc": "Displays info about built-in bash commands.", "example": "help cd | less", "category": "System"},
    "chmod": {"desc": "Changes read/write/execute permissions.", "example": "chmod +x *.sh", "category": "System"}
}

def load_json(filepath, default_val):
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            pass
    return default_val

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def write_log(cmd, reason, raw_output=""):
    """Writes failed probes to the debug log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(DEBUG_LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {cmd} | {reason}\n")
        if raw_output:
            clean_out = raw_output.strip()[:150].replace('\n', ' ')
            f.write(f"    -> RAW: {clean_out}...\n")

session_history = load_json(HISTORY_FILE, [])
custom_guide = load_json(CUSTOM_DICT_FILE, {})
probe_blacklist = load_json(BLACKLIST_FILE, [])

def get_all_known_commands():
    return {**BEGINNER_GUIDE, **custom_guide}

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def pause():
    input(f"\n{YELLOW}Press Enter to continue...{RESET}")

def suggest_command(bad_cmd):
    known_cmds = list(get_all_known_commands().keys())
    matches = difflib.get_close_matches(bad_cmd, known_cmds, n=1, cutoff=0.6)
    return matches[0] if matches else None

def print_dashboard():
    clear_screen()
    print(f"{CYAN}{BOLD}=============================================={RESET}")
    print(f"{CYAN}{BOLD}      Terminal Command Explorer & Tutor       {RESET}")
    print(f"{CYAN}{BOLD}=============================================={RESET}")

    if session_history:
        print(f"{MAGENTA}Recent: {', '.join(session_history[-5:])}{RESET}\n")

    print(f" {GREEN}[1]{RESET} Explore Random Command")
    print(f" {GREEN}[2]{RESET} Explore by Category")
    print(f" {GREEN}[3]{RESET} Manage Custom Imports")
    print(f" {MAGENTA}[4]{RESET} Auto-Scan System for Commands")
    print(f" {YELLOW}[5]{RESET} View Debug Log")
    print(f" {RED}[6]{RESET} Factory Reset (Wipe Data)")
    print(f" {RED}[0]{RESET} Exit & Quiz Mode")
    print(f"{YELLOW}Or type a command to search (e.g., ls, nano){RESET}\n")

def view_debug_log():
    """Reads and displays the last 30 lines of the debug log."""
    clear_screen()
    print(f"{YELLOW}★ Heuristic Debug Log ★{RESET}\n")
    if DEBUG_LOG_FILE.exists():
        with open(DEBUG_LOG_FILE, "r") as f:
            lines = f.readlines()
            if not lines:
                print("Log is empty.")
            for line in lines[-30:]:
                print(line, end="")
    else:
        print(f"{GREEN}No logs exist yet. Run an Auto-Scan!{RESET}")
    print("\n")
    pause()

def factory_reset():
    """Allows the user to easily wipe specific states."""
    clear_screen()
    global session_history, custom_guide, probe_blacklist

    print(f"{RED}★ Factory Reset ★{RESET}\n")
    print(f" {GREEN}[1]{RESET} Clear Session History")
    print(f" {GREEN}[2]{RESET} Clear Probe Blacklist")
    print(f" {GREEN}[3]{RESET} Clear Custom Imported Commands")
    print(f" {RED}[4]{RESET} NUKE ALL DATA")
    print(f" {YELLOW}[0]{RESET} Cancel")

    choice = input(f"\n{GREEN}➜ {RESET}").strip()

    if choice == '1':
        session_history = []
        save_json(HISTORY_FILE, session_history)
        print(f"{YELLOW}History cleared.{RESET}")
    elif choice == '2':
        probe_blacklist = []
        save_json(BLACKLIST_FILE, probe_blacklist)
        print(f"{YELLOW}Blacklist cleared.{RESET}")
    elif choice == '3':
        custom_guide = {}
        save_json(CUSTOM_DICT_FILE, custom_guide)
        print(f"{YELLOW}Custom imports cleared.{RESET}")
    elif choice == '4':
        session_history, custom_guide, probe_blacklist = [], {}, []
        save_json(HISTORY_FILE, session_history)
        save_json(CUSTOM_DICT_FILE, custom_guide)
        save_json(BLACKLIST_FILE, probe_blacklist)
        if DEBUG_LOG_FILE.exists():
            DEBUG_LOG_FILE.unlink()
        print(f"{RED}All databases and logs nuked.{RESET}")

    if choice in ['1', '2', '3', '4']:
        pause()

def explore_category():
    all_known = get_all_known_commands()
    categories = sorted(list(set(data["category"] for data in all_known.values())))

    clear_screen()
    print(f"{MAGENTA}★ Categories ★{RESET}\n")
    for idx, cat in enumerate(categories, 1):
        print(f" {GREEN}[{idx}]{RESET} {cat}")
    print(f" {RED}[0]{RESET} Cancel")

    try:
        choice = input(f"\nSelect a category number: {GREEN}➜ {RESET}").strip()
        if choice == '0' or not choice.isdigit():
            return
        idx = int(choice) - 1
        if 0 <= idx < len(categories):
            selected_cat = categories[idx]
            clear_screen()
            print(f"{YELLOW}--- {selected_cat} Commands ---{RESET}\n")
            for cmd, data in all_known.items():
                if data["category"] == selected_cat:
                    print(f" • {CYAN}{BOLD}{cmd}{RESET}: {data['desc']}")
            pause()
        else:
            print(f"{RED}Invalid selection.{RESET}")
            pause()
    except KeyboardInterrupt:
        return

def manage_imports():
    clear_screen()
    if not custom_guide:
        print(f"{YELLOW}No custom commands imported yet.{RESET}")
        pause()
        return

    print(f"{MAGENTA}★ Custom Imported Libraries ★{RESET}\n")
    for cmd, data in custom_guide.items():
        short_desc = (data['desc'][:60] + '...') if len(data['desc']) > 60 else data['desc']
        print(f" • {CYAN}{BOLD}{cmd}{RESET}: {short_desc}")

    print(f"\n{YELLOW}Options:{RESET}")
    print(f" - Type a command name to {RED}DELETE{RESET} it from the database.")
    print(f" - Press Enter to return to the menu.")

    choice = input(f"\n{GREEN}➜ {RESET}").strip().lower()
    if choice in custom_guide:
        del custom_guide[choice]
        save_json(CUSTOM_DICT_FILE, custom_guide)
        print(f"{YELLOW}Successfully deleted '{choice}'.{RESET}")
        pause()
    elif choice:
        print(f"{RED}Command not found in custom imports.{RESET}")
        pause()

def auto_scan_system():
    clear_screen()
    print(f"{MAGENTA}★ System Auto-Scanner ★{RESET}\n")
    print(f"Scanning system PATH for unknown executables...")

    all_known = get_all_known_commands()
    system_bins = []

    for path_dir in os.environ.get('PATH', '').split(os.pathsep):
        if os.path.isdir(path_dir):
            for file in os.listdir(path_dir):
                full_path = os.path.join(path_dir, file)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    if file not in all_known and file not in system_bins and file not in probe_blacklist:
                        system_bins.append(file)

    if not system_bins:
        print(f"{GREEN}Wow! Your database maps every executable in your PATH.{RESET}")
        pause()
        return

    # Bumped the batch size up to 50
    batch_size = min(50, len(system_bins))
    scan_batch = random.sample(system_bins, batch_size)

    print(f"Found {len(system_bins)} unknown/untested tools. Probing batch of {batch_size}...\n")

    successful_imports = 0
    reject_terms = [
        "usage:", "options:", "params", "or:", "[option]",
        "not found", "no such file", "command not found",
        "can't locate", "no module named", "traceback", "exception"
    ]
    reject_chars = ["[", "---", "<"]

    for cmd in scan_batch:
        try:
            process = subprocess.run([cmd, '--help'], capture_output=True, text=True, timeout=0.5)
            output = process.stdout + process.stderr
            lines = [line.strip() for line in output.splitlines() if line.strip()]

            success = False
            for line in lines[:20]:
                lower_line = line.lower()
                if len(line) > 15 and not any(t in lower_line for t in reject_terms) and not any(c in line for c in reject_chars) and not line.strip().startswith("-"):
                    custom_guide[cmd] = {
                        "desc": line,
                        "example": f"{cmd} --help",
                        "category": "Auto-Imported Libs"
                    }
                    print(f" {GREEN}[+]{RESET} Imported: {CYAN}{cmd}{RESET}")
                    successful_imports += 1
                    success = True
                    break

            if not success:
                probe_blacklist.append(cmd)
                write_log(cmd, "Heuristic Reject", output)

        except subprocess.TimeoutExpired as e:
            probe_blacklist.append(cmd)
            write_log(cmd, "Timeout (Likely interactive)", "")
        except Exception as e:
            probe_blacklist.append(cmd)
            write_log(cmd, "Execution Error", str(e))

    if successful_imports > 0:
        save_json(CUSTOM_DICT_FILE, custom_guide)
        print(f"\n{GREEN}Successfully harvested {successful_imports} new commands!{RESET}")
    else:
        print(f"\n{YELLOW}Sweep finished. Tested tools were either interactive or lacked definitions.{RESET}")

    save_json(BLACKLIST_FILE, probe_blacklist)
    pause()

def run_quiz():
    if len(session_history) < 3:
        print(f"\n{YELLOW}Not enough history for a quiz yet. Keep exploring!{RESET}")
        return

    clear_screen()
    print(f"{MAGENTA}★ Final Exam: Quiz Mode ★{RESET}\n")

    quiz_pool = list(set(session_history))
    random.shuffle(quiz_pool)
    questions = quiz_pool[:3]
    score = 0
    all_data = get_all_known_commands()

    for q_cmd in questions:
        if q_cmd not in all_data:
            continue

        print(f"{CYAN}Question:{RESET} Which command does the following?")
        print(f"-> \"{all_data[q_cmd]['desc']}\"")
        ans = input(f"{GREEN}Your answer: {RESET}").strip().lower()

        if ans == q_cmd:
            print(f"{GREEN}Correct!{RESET}\n")
            score += 1
        else:
            print(f"{RED}Incorrect.{RESET} The answer was '{BOLD}{q_cmd}{RESET}'.\n")

    print(f"{YELLOW}Quiz Complete! You scored {score}/3.{RESET}")
    pause()

def search_command(base_command):
    clear_screen()
    all_known = get_all_known_commands()

    if base_command not in session_history:
        session_history.append(base_command)
        save_json(HISTORY_FILE, session_history)

    if base_command in all_known:
        data = all_known[base_command]
        print(f"{CYAN}Command:{RESET} {base_command}")
        print(f"Category:    [{MAGENTA}{data['category']}{RESET}]")
        print(f"Explanation: {data['desc']}")
        print(f"Example:     {data['example']}")
        pause()
        return

    try:
        process = subprocess.run(['whatis', base_command], capture_output=True, text=True, check=True)
        print(f"{CYAN}Command:{RESET} {base_command}")
        print(f"Explanation (OS Manual): {process.stdout.strip()}")
        pause()
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        process = subprocess.run(['bash', '-c', 'help -d "$1"', '_', base_command], capture_output=True, text=True, check=True)
        desc = process.stdout.strip()
        if desc:
            print(f"{CYAN}Command:{RESET} {base_command}")
            print(f"Explanation (Built-in): {desc}")
            pause()
            return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if shutil.which(base_command):
        try:
            process = subprocess.run([base_command, '--help'], capture_output=True, text=True, timeout=2)
            output = process.stdout + process.stderr
            lines = [line.strip() for line in output.splitlines() if line.strip()]

            description = "An installed program. No readable description found."
            reject_terms = [
                "usage:", "options:", "params", "or:", "[option]",
                "not found", "no such file", "command not found",
                "can't locate", "no module named", "traceback", "exception"
            ]
            reject_chars = ["[", "---", "<"]

            success = False
            for line in lines[:20]:
                lower_line = line.lower()
                if len(line) > 15 and not any(t in lower_line for t in reject_terms) and not any(c in line for c in reject_chars) and not line.strip().startswith("-"):
                    description = line
                    success = True
                    break

            if success:
                print(f"{CYAN}Command:{RESET} {base_command}")
                print(f"Explanation (Auto-probed): {description}")
                print(f"{MAGENTA}[!] Successfully imported into local dictionary.{RESET}")

                custom_guide[base_command] = {
                    "desc": description,
                    "example": f"{base_command} --help",
                    "category": "Auto-Imported Libs"
                }
                save_json(CUSTOM_DICT_FILE, custom_guide)
            else:
                print(f"{CYAN}Command:{RESET} {base_command}")
                print(f"{RED}Explanation:{RESET} Program ran, but heuristic rejected output.")
                write_log(base_command, "Manual Search Reject", output)

            pause()
            return

        except subprocess.TimeoutExpired:
            print(f"{RED}Explanation:{RESET} Program timed out. It might be interactive.")
            write_log(base_command, "Manual Search Timeout", "")
            if base_command not in probe_blacklist:
                probe_blacklist.append(base_command)
                save_json(BLACKLIST_FILE, probe_blacklist)
            pause()
            return
        except Exception as e:
            write_log(base_command, "Manual Search Error", str(e))
            pass

    print(f"{RED}Error:{RESET} Couldn't find info for '{base_command}'.")
    suggestion = suggest_command(base_command)
    if suggestion:
        print(f"{YELLOW}Linting Suggestion:{RESET} Did you mean '{BOLD}{GREEN}{suggestion}{RESET}'?")

    if session_history and session_history[-1] == base_command:
        session_history.pop()
        save_json(HISTORY_FILE, session_history)
    pause()

def main_loop():
    while True:
        print_dashboard()
        try:
            raw_input = input(f"{GREEN}➜ {RESET}").strip()
        except KeyboardInterrupt:
            clear_screen()
            print(f"{YELLOW}Terminating... Happy coding!{RESET}\n")
            sys.exit(0)

        if not raw_input:
            continue

        if raw_input == '1':
            cmd = random.choice(list(get_all_known_commands().keys()))
            search_command(cmd)
            continue
        elif raw_input == '2':
            explore_category()
            continue
        elif raw_input == '3':
            manage_imports()
            continue
        elif raw_input == '4':
            auto_scan_system()
            continue
        elif raw_input == '5':
            view_debug_log()
            continue
        elif raw_input == '6':
            factory_reset()
            continue
        elif raw_input == '0' or raw_input.lower() == 'done':
            choice = input(f"\n{YELLOW}Do you want to take a quick quiz on your history before leaving? (y/n): {RESET}").strip().lower()
            if choice == 'y':
                run_quiz()
            clear_screen()
            print(f"{YELLOW}Exiting... Happy coding!{RESET}\n")
            break

        command_tokens = raw_input.lower().split()
        search_command(command_tokens[0])

if __name__ == "__main__":
    main_loop()
