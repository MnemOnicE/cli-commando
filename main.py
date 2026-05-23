import urllib.request
import urllib.error
import subprocess
import shutil
import random
import sys
import os
import re
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
PENDING_DICT_FILE = BASE_DIR / "pending.json"
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

session_history = load_json(HISTORY_FILE, {})
if isinstance(session_history, list):
    session_history = {cmd: 0 for cmd in session_history}
custom_guide = load_json(CUSTOM_DICT_FILE, {})
probe_blacklist = load_json(BLACKLIST_FILE, [])
pending_imports = load_json(PENDING_DICT_FILE, {})

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

def search_intent(query):
    query_words = set(re.findall(r'\w+', query.lower()))
    stop_words = {"the", "a", "to", "and", "or", "of", "in", "for", "is", "on", "with", "how"}
    query_words = query_words - stop_words

    if not query_words:
        return []

    all_known = get_all_known_commands()
    results = {}

    for cmd, data in all_known.items():
        desc_words = set(re.findall(r'\w+', data['desc'].lower()))
        desc_words = desc_words - stop_words

        # Calculate overlap
        intersection = query_words.intersection(desc_words)
        if intersection:
            results[cmd] = len(intersection)

    # Sort by number of matched words
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return [cmd for cmd, score in sorted_results[:5]]

def print_dashboard():
    clear_screen()
    print(f"{CYAN}{BOLD}=============================================={RESET}")
    print(f"{CYAN}{BOLD}      Terminal Command Explorer & Tutor       {RESET}")
    print(f"{CYAN}{BOLD}=============================================={RESET}")

    if session_history:
        print(f"{MAGENTA}Recent: {', '.join(list(session_history.keys())[-5:])}{RESET}\n")

    print(f" {GREEN}[1]{RESET} Explore Random Command")
    print(f" {GREEN}[2]{RESET} Explore by Category")
    print(f" {GREEN}[3]{RESET} Manage Custom Imports")
    print(f" {MAGENTA}[4]{RESET} Auto-Scan System for Commands")
    print(f" {YELLOW}[5]{RESET} View Debug Log")
    print(f" {RED}[6]{RESET} Factory Reset (Wipe Data)")
    if pending_imports:
        print(f" {CYAN}[7]{RESET} Review Pending Imports ({len(pending_imports)} waiting)")
    print(f" {MAGENTA}[8]{RESET} Install Bash Hook")
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
        session_history = {}
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

    allowed_paths = ['/data/data/com.termux/files/usr/bin', '/system/bin', '/bin', '/usr/bin']
    for path_dir in os.environ.get('PATH', '').split(os.pathsep):
        if path_dir not in allowed_paths:
            continue
        if os.path.isdir(path_dir):
            for file in os.listdir(path_dir):
                full_path = os.path.join(path_dir, file)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    if file not in all_known and file not in system_bins and file not in probe_blacklist and file not in pending_imports:
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
        # Layer 1: OS Query
        try:
            process = subprocess.run(['whatis', cmd], capture_output=True, text=True, errors='replace', check=True)
            desc = process.stdout.strip()
            pending_imports[cmd] = {
                "desc": desc,
                "example": f"{cmd} --help",
                "category": "Auto-Imported Libs"
            }
            print(f" {GREEN}[+]{RESET} Added to pending (OS Manual): {CYAN}{cmd}{RESET}")
            successful_imports += 1
            continue
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        try:
            process = subprocess.run(['bash', '-c', 'help -d "$1"', '_', cmd], capture_output=True, text=True, errors='replace', check=True)
            desc = process.stdout.strip()
            if desc:
                pending_imports[cmd] = {
                    "desc": desc,
                    "example": f"{cmd} --help",
                    "category": "Auto-Imported Libs"
                }
                print(f" {GREEN}[+]{RESET} Added to pending (Built-in): {CYAN}{cmd}{RESET}")
                successful_imports += 1
                continue
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Layer 2: Execution Fallback
        try:
            process = subprocess.run([cmd, '--help'], capture_output=True, text=True, errors='replace', timeout=0.2)
            output = process.stdout + process.stderr
            lines = [line.strip() for line in output.splitlines() if line.strip()]

            success = False
            description = "An installed program. No readable description found."
            example_str = f"{cmd} --help"

            # Boom's regex motifs (Examples-First Priority)
            motif_dash = re.compile(r"(?i)^\s*" + re.escape(cmd) + r"\s+-\s+(.*)")

            # Try to find an example block
            for i, line in enumerate(lines):
                lower_line = line.lower()
                if "example:" in lower_line or "examples:" in lower_line or "usage:" in lower_line:
                    # Look at next few lines for the actual command snippet
                    for j in range(1, 4):
                        if i+j < len(lines):
                            candidate = lines[i+j].strip()
                            if candidate and not candidate.startswith("-") and cmd in candidate:
                                example_str = candidate
                                success = True
                                break
                    if success:
                        break

            # Now find description
            for line in lines[:20]:
                match_dash = motif_dash.search(line)
                if match_dash:
                    description = match_dash.group(1).strip()
                    success = True
                    break

            if not success:
                for line in lines[:20]:
                    lower_line = line.lower()
                    if len(line) > 15 and not any(t in lower_line for t in reject_terms) and not any(c in line for c in reject_chars) and not line.strip().startswith("-"):
                        description = f"[Low Confidence] {line}"
                        success = True
                        break

            if success:
                pending_imports[cmd] = {
                    "desc": description,
                    "example": example_str,
                    "category": "Auto-Imported Libs"
                }
                print(f" {GREEN}[+]{RESET} Added to pending (Regex/Heuristic): {CYAN}{cmd}{RESET}")
                successful_imports += 1

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
        save_json(PENDING_DICT_FILE, pending_imports)
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

    quiz_pool = list(session_history.keys())
    all_data = get_all_known_commands()

    # Filter pool to only known commands
    valid_pool = [cmd for cmd in quiz_pool if cmd in all_data]
    if len(valid_pool) < 3:
        print(f"\n{YELLOW}Not enough valid known commands for a quiz yet. Keep exploring!{RESET}")
        pause()
        return

    # Weighted random selection for spaced repetition
    weights = []
    for cmd in valid_pool:
        score = session_history.get(cmd, 0)
        if score == 0:
            weights.append(50)
        elif score == 1:
            weights.append(30)
        elif score == 2:
            weights.append(15)
        elif score == 3:
            weights.append(5)
        elif score == 4:
            weights.append(2)
        else: # score >= 5
            weights.append(1)

    try:
        # Choose 3 unique questions based on weights
        questions = []
        pool_copy = list(valid_pool)
        weights_copy = list(weights)
        for _ in range(min(3, len(valid_pool))):
            q = random.choices(pool_copy, weights=weights_copy, k=1)[0]
            idx = pool_copy.index(q)
            questions.append(q)
            pool_copy.pop(idx)
            weights_copy.pop(idx)
    except Exception:
        # Fallback to random if something goes wrong
        random.shuffle(valid_pool)
        questions = valid_pool[:3]

    score = 0

    for q_cmd in questions:
        print(f"{CYAN}Question:{RESET} Which command does the following?")
        print(f"-> \"{all_data[q_cmd]['desc']}\"")
        ans = input(f"{GREEN}Your answer: {RESET}").strip().lower()

        if ans == q_cmd:
            print(f"{GREEN}Correct!{RESET}\n")
            session_history[q_cmd] = min(5, session_history.get(q_cmd, 0) + 1)
            score += 1
        else:
            print(f"{RED}Incorrect.{RESET} The answer was '{BOLD}{q_cmd}{RESET}'.\n")
            session_history[q_cmd] = 0

    save_json(HISTORY_FILE, session_history)
    print(f"{YELLOW}Quiz Complete! You scored {score}/3.{RESET}")
    pause()

def search_command(base_command, headless=False, audit=False):
    if audit:
        # Kinetic audit via strace
        if not shutil.which(base_command):
            if headless:
                print(json.dumps({"command": base_command, "status": "not_found", "desc": "Audit failed, binary not found."}))
            else:
                print(f"{RED}Error:{RESET} Audit failed, '{base_command}' not found in PATH.")
            return

        if not headless:
            print(f"{RED}{BOLD}WARNING: Audit mode will execute '{base_command}' to observe its behavior.{RESET}")
            print(f"{RED}This is potentially destructive for commands like 'rm' or 'reboot'.{RESET}")
            choice = input(f"{YELLOW}Proceed? (y/n): {RESET}").strip().lower()
            if choice != 'y':
                return
            print(f"\n{MAGENTA}★ Running Kinetic Audit on '{base_command}' ★{RESET}")

        try:
            # Wrap the binary in a linux system call tracer to trace file, network, process syscalls
            process = subprocess.run(
                ['strace', '-e', 'trace=file,network,process', 'timeout', '0.5s', base_command],
                capture_output=True, text=True, errors='replace'
            )
            out = process.stderr # strace outputs to stderr

            tags = set()
            if '/dev/' in out:
                tags.add('[Hardware Interfacing]')
            if 'socket(' in out or 'connect(' in out or 'bind(' in out:
                tags.add('[Network Mutator]')
            if 'clone(' in out or 'execve(' in out or 'fork(' in out:
                tags.add('[Process Spawner]')
            if 'openat(' in out or 'open(' in out:
                tags.add('[File Reader/Writer]')

            tag_str = ", ".join(tags) if tags else "[Pure Compute / Minimal Syscalls]"

            if headless:
                print(json.dumps({"command": base_command, "status": "audited", "kinetic_tags": list(tags)}))
            else:
                print(f"{CYAN}Audit Results for:{RESET} {base_command}")
                print(f"Tags: {YELLOW}{tag_str}{RESET}")
                pause()
            return
        except FileNotFoundError:
            if headless:
                print(json.dumps({"command": base_command, "status": "error", "desc": "strace not installed"}))
            else:
                print(f"{RED}Error:{RESET} 'strace' is required for audit mode but not installed.")
                pause()
            return

    if not headless:
        clear_screen()
    all_known = get_all_known_commands()

    global session_history
    if base_command not in session_history:
        session_history[base_command] = 0
    else:
        # Move to end (LRU)
        session_history[base_command] = session_history.pop(base_command)

    while len(session_history) > 500:
        del session_history[next(iter(session_history))]

    if base_command in all_known:
        data = all_known[base_command]

        # LRU cache: If it's a custom command, pop and re-insert
        if base_command in custom_guide:
            custom_guide[base_command] = custom_guide.pop(base_command)
            save_json(CUSTOM_DICT_FILE, custom_guide)

        if headless:
            path = shutil.which(base_command) or "built-in"
            print(json.dumps({"command": base_command, "status": "found", "desc": data['desc'], "path": path}))
            return

        print(f"{CYAN}Command:{RESET} {base_command}")
        print(f"Category:    [{MAGENTA}{data['category']}{RESET}]")
        print(f"Explanation: {data['desc']}")
        print(f"Example:     {data['example']}")
        pause()
        return

    try:
        process = subprocess.run(['whatis', base_command], capture_output=True, text=True, errors='replace', check=True)
        desc = process.stdout.strip()
        if headless:
            path = shutil.which(base_command) or "built-in"
            print(json.dumps({"command": base_command, "status": "found", "desc": desc, "path": path}))
            return

        print(f"{CYAN}Command:{RESET} {base_command}")
        print(f"Explanation (OS Manual): {desc}")
        pause()
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        process = subprocess.run(['bash', '-c', 'help -d "$1"', '_', base_command], capture_output=True, text=True, errors='replace', check=True)
        desc = process.stdout.strip()
        if desc:
            if headless:
                print(json.dumps({"command": base_command, "status": "found", "desc": desc, "path": "built-in"}))
                return

            print(f"{CYAN}Command:{RESET} {base_command}")
            print(f"Explanation (Built-in): {desc}")
            pause()
            return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if shutil.which(base_command):
        # Palette's tldr API Fallback
        try:
            tldr_text = None
            urls = [
                f"https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/{base_command}.md",
                f"https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/linux/{base_command}.md"
            ]
            for url in urls:
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=1.5) as response:
                        tldr_text = response.read().decode('utf-8')
                        break
                except urllib.error.URLError:
                    continue

            if tldr_text:
                tldr_lines = tldr_text.splitlines()

                desc_lines = [l.strip(">").strip() for l in tldr_lines if l.startswith(">")]
                desc = " ".join(desc_lines) if desc_lines else f"A command ({base_command})"

                example_lines = [l.strip("`") for l in tldr_lines if l.startswith("`")]
                example_str = example_lines[0] if example_lines else f"{base_command} --help"

                if headless:
                    print(json.dumps({"command": base_command, "status": "found", "desc": desc, "path": shutil.which(base_command)}))
                    return

                print(f"{CYAN}Command:{RESET} {base_command}")
                print(f"Explanation (TLDR): {desc}")
                print(f"Example (TLDR): {example_str}")
                print(f"{MAGENTA}[!] Successfully imported into local dictionary.{RESET}")

                pending_imports[base_command] = {
                    "desc": desc,
                    "example": example_str,
                    "category": "Auto-Imported Libs"
                }
                save_json(PENDING_DICT_FILE, pending_imports)
                if not headless:
                    pause()
                return
        except urllib.error.URLError:
            pass
        except Exception:
            pass

        try:
            process = subprocess.run([base_command, '--help'], capture_output=True, text=True, errors='replace', timeout=2)
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
            description = "An installed program. No readable description found."
            example_str = f"{base_command} --help"

            # Boom's regex motifs (Examples-First Priority)
            motif_dash = re.compile(r"(?i)^\s*" + re.escape(base_command) + r"\s+-\s+(.*)")

            # Try to find an example block
            for i, line in enumerate(lines):
                lower_line = line.lower()
                if "example:" in lower_line or "examples:" in lower_line or "usage:" in lower_line:
                    # Look at next few lines for the actual command snippet
                    for j in range(1, 4):
                        if i+j < len(lines):
                            candidate = lines[i+j].strip()
                            if candidate and not candidate.startswith("-") and base_command in candidate:
                                example_str = candidate
                                success = True
                                break
                    if success:
                        break

            # Now find description
            for line in lines[:20]:
                match_dash = motif_dash.search(line)
                if match_dash:
                    description = match_dash.group(1).strip()
                    success = True
                    break

            if not success:
                for line in lines[:20]:
                    lower_line = line.lower()
                    if len(line) > 15 and not any(t in lower_line for t in reject_terms) and not any(c in line for c in reject_chars) and not line.strip().startswith("-"):
                        description = f"[Low Confidence] {line}"
                        success = True
                        break

            if success:
                if headless:
                    print(json.dumps({"command": base_command, "status": "found", "desc": description, "path": shutil.which(base_command)}))
                    return

                print(f"{CYAN}Command:{RESET} {base_command}")
                print(f"Explanation (Auto-probed): {description}")
                print(f"{MAGENTA}[!] Successfully imported into local dictionary.{RESET}")

                # Instead of putting it directly to custom_guide, we should put it to pending_imports according to Boom's fix rules
                pending_imports[base_command] = {
                    "desc": description,
                    "example": example_str,
                    "category": "Auto-Imported Libs"
                }
                save_json(PENDING_DICT_FILE, pending_imports)
            else:
                if headless:
                    print(json.dumps({"command": base_command, "status": "heuristic_rejected", "desc": "Program ran, but heuristic rejected output.", "path": shutil.which(base_command)}))
                    return

                print(f"{CYAN}Command:{RESET} {base_command}")
                print(f"{RED}Explanation:{RESET} Program ran, but heuristic rejected output.")
                write_log(base_command, "Manual Search Reject", output)

            if not headless:
                pause()
            return

        except subprocess.TimeoutExpired:
            if headless:
                print(json.dumps({"command": base_command, "status": "timeout", "desc": "Program timed out. It might be interactive.", "path": shutil.which(base_command)}))
                return

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

    if headless:
        print(json.dumps({"command": base_command, "status": "not_found", "desc": "Couldn't find exact command info.", "path": None}))
        return

    print(f"{RED}Error:{RESET} Couldn't find exact command '{base_command}'.")

    intent_results = search_intent(base_command)
    if intent_results:
        print(f"\n{CYAN}Intent Search:{RESET} Did you mean one of these?")
        for r in intent_results:
            data = get_all_known_commands()[r]
            print(f" - {GREEN}{r}{RESET}: {data['desc']}")
        print()
    else:
        suggestion = suggest_command(base_command)
        if suggestion:
            print(f"{YELLOW}Linting Suggestion:{RESET} Did you mean '{BOLD}{GREEN}{suggestion}{RESET}'?")

    if session_history and list(session_history.keys())[-1] == base_command:
        del session_history[base_command]
    pause()


def review_pending_imports():
    global custom_guide, probe_blacklist, pending_imports
    if not pending_imports:
        print(f"{YELLOW}No pending imports to review.{RESET}")
        pause()
        return

    clear_screen()
    print(f"{MAGENTA}★ Review Pending Imports ★{RESET}\n")

    commands_to_review = list(pending_imports.keys())

    for cmd in commands_to_review:
        clear_screen()
        data = pending_imports[cmd]
        print(f"{CYAN}Command:{RESET} {cmd}")
        print(f"Category:    [{MAGENTA}{data['category']}{RESET}]")
        print(f"Explanation: {data['desc']}")
        print(f"Example:     {data['example']}")
        print(f"\n{YELLOW}Options:{RESET} (y) Accept | (n) Reject | (e) Edit | (q) Quit Reviewing")

        while True:
            choice = input(f"{GREEN}➜ {RESET}").strip().lower()
            if choice == 'y':
                custom_guide[cmd] = data
                if len(custom_guide) > 1000:
                    del custom_guide[next(iter(custom_guide))]
                save_json(CUSTOM_DICT_FILE, custom_guide)
                del pending_imports[cmd]
                save_json(PENDING_DICT_FILE, pending_imports)
                print(f"{GREEN}Accepted {cmd}.{RESET}")
                break
            elif choice == 'n':
                probe_blacklist.append(cmd)
                save_json(BLACKLIST_FILE, probe_blacklist)
                del pending_imports[cmd]
                save_json(PENDING_DICT_FILE, pending_imports)
                print(f"{RED}Rejected {cmd}.{RESET}")
                break
            elif choice == 'e':
                new_desc = input(f"{CYAN}Enter new explanation for '{cmd}': {RESET}").strip()
                if new_desc:
                    data['desc'] = new_desc
                    custom_guide[cmd] = data
                    if len(custom_guide) > 1000:
                        del custom_guide[next(iter(custom_guide))]
                    save_json(CUSTOM_DICT_FILE, custom_guide)
                    del pending_imports[cmd]
                    save_json(PENDING_DICT_FILE, pending_imports)
                    print(f"{GREEN}Accepted {cmd} with edited description.{RESET}")
                else:
                    print(f"{YELLOW}Edit cancelled.{RESET}")
                break
            elif choice == 'q':
                return
            else:
                print(f"{RED}Invalid choice.{RESET}")

    print(f"\n{GREEN}Finished reviewing pending imports.{RESET}")
    pause()


def install_bash_hook():
    clear_screen()
    print(f"{MAGENTA}★ Install Bash Hook ★{RESET}\n")
    print("This will add a 'command_not_found_handle' to your ~/.bashrc.")
    print("When you type an unknown command, it will automatically be searched in cli-commando.")

    choice = input(f"\n{YELLOW}Proceed? (y/n): {RESET}").strip().lower()
    if choice == 'y':
        bashrc_path = os.path.expanduser("~/.bashrc")
        script_path = os.path.abspath(__file__)

        hook_snippet = f'''\n# cli-commando auto-search hook
command_not_found_handle() {{
    python3 "{script_path}" "$1"
    return 127
}}
'''
        # Check if already installed
        try:
            with open(bashrc_path, "r") as f:
                if "command_not_found_handle()" in f.read() and "cli-commando" in f.read():
                    print(f"\n{YELLOW}Hook is already installed in ~/.bashrc.{RESET}")
                    pause()
                    return
        except FileNotFoundError:
            pass

        with open(bashrc_path, "a") as f:
            f.write(hook_snippet)

        print(f"\n{GREEN}Successfully added hook to ~/.bashrc.{RESET}")
        print(f"Please run 'source ~/.bashrc' or restart your terminal for it to take effect.")
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
        elif raw_input == '7' and pending_imports:
            review_pending_imports()
            continue
        elif raw_input == '8':
            install_bash_hook()
            continue
        elif raw_input == '0' or raw_input.lower() == 'done':
            choice = input(f"\n{YELLOW}Do you want to take a quick quiz on your history before leaving? (y/n): {RESET}").strip().lower()
            if choice == 'y':
                run_quiz()
            clear_screen()
            save_json(HISTORY_FILE, session_history)
            print(f"{YELLOW}Exiting... Happy coding!{RESET}\n")
            break

        command_tokens = raw_input.lower().split()
        search_command(command_tokens[0])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="cli-commando")
    parser.add_argument('command', nargs='*', help='Command to search for or execute')
    parser.add_argument('--json', action='store_true', help='Output in JSON format (headless mode)')
    parser.add_argument('--audit', action='store_true', help='Run kinetic audit using strace')

    args, unknown = parser.parse_known_args()

    if not args.command and not unknown:
        main_loop()
    else:
        headless = args.json
        audit_mode = args.audit
        cmd_list = args.command + unknown

        if cmd_list and cmd_list[0] == 'search':
            cmd_list.pop(0)

        if cmd_list:
            search_command(' '.join(cmd_list), headless=headless, audit=audit_mode)
        else:
            main_loop()
