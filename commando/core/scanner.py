import concurrent.futures
import difflib
import os
import random
import re
import subprocess

from commando.utils.config import ConfigManager
from commando.utils.io import (
    BASE_DIR,
    CYAN,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    clear_screen,
    pause,
    save_json,
)

INDEX_FILE = BASE_DIR / "index.json"


def sanitize_text(text):
    # Whitelist printable ASCII, UTF-8 printables, and valid whitespace (newline, tab)
    # Rejects control characters, ANSI escapes, etc.
    if not text:
        return text

    sanitized = []
    for char in text:
        code = ord(char)
        # 9: tab, 10: newline, 13: carriage return
        # 32-126: printable ASCII
        # > 127: UTF-8 standard characters (excluding C1 control codes 128-159)
        if code in (9, 10, 13) or (32 <= code <= 126) or (code >= 160):
            sanitized.append(char)
    return "".join(sanitized)


def build_inverted_index(state_manager):
    index = {}
    all_known = state_manager.get_all_known_commands()
    stop_words = {
        "the",
        "a",
        "to",
        "and",
        "or",
        "of",
        "in",
        "for",
        "is",
        "on",
        "with",
        "how",
    }

    for cmd, data in all_known.items():
        desc_words = set(re.findall(r"\w+", data["desc"].lower())) - stop_words
        for word in desc_words:
            if word not in index:
                index[word] = []
            if cmd not in index[word]:
                index[word].append(cmd)

    save_json(INDEX_FILE, index)
    return index


def get_inverted_index(state_manager):
    # For now, just rebuild it if it doesn't exist, or just rebuild it to be safe
    # In a fully optimized app, we'd invalidate it on add/remove.
    return build_inverted_index(state_manager)


def search_intent(query, state_manager):
    query_words = set(re.findall(r"\w+", query.lower()))
    stop_words = {
        "the",
        "a",
        "to",
        "and",
        "or",
        "of",
        "in",
        "for",
        "is",
        "on",
        "with",
        "how",
    }
    query_words = query_words - stop_words

    if not query_words:
        return []

    index = get_inverted_index(state_manager)
    results = {}

    for word in query_words:
        if word in index:
            for cmd in index[word]:
                results[cmd] = results.get(cmd, 0) + 1

    # Sort by number of matched words
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return [cmd for cmd, score in sorted_results[:5]]


def suggest_command(bad_cmd, state_manager):
    known_cmds = list(state_manager.get_all_known_commands().keys())
    matches = difflib.get_close_matches(bad_cmd, known_cmds, n=1, cutoff=0.6)
    return matches[0] if matches else None


def auto_scan_system(state_manager):
    clear_screen()
    print(f"{MAGENTA}★ System Auto-Scanner ★{RESET}\n")
    print("Scanning system PATH for unknown executables...")

    all_known_keys = set(state_manager.get_all_known_commands().keys())
    probe_blacklist_set = set(state_manager.probe_blacklist)
    pending_imports_set = set(state_manager.pending_imports.keys())
    system_bins_set = set()

    allowed_paths = ConfigManager().get("allowed_paths")
    if not isinstance(allowed_paths, list):
        allowed_paths = []
    raw_path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    path_dirs = []
    for p in raw_path_dirs:
        norm_p = os.path.realpath(os.path.normpath(os.path.expanduser(p)))
        if norm_p in allowed_paths and norm_p not in path_dirs:
            path_dirs.append(norm_p)
    for path_dir in path_dirs:
        if os.path.isdir(path_dir):
            for file in os.listdir(path_dir):
                full_path = os.path.join(path_dir, file)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    if (
                        file not in all_known_keys
                        and file not in system_bins_set
                        and file not in probe_blacklist_set
                        and file not in pending_imports_set
                    ):
                        system_bins_set.add(file)

    if not system_bins_set:
        print(f"{GREEN}Wow! Your database maps every executable in your PATH.{RESET}")
        pause()
        return

    system_bins = list(system_bins_set)
    batch_size = min(50, len(system_bins))
    scan_batch = random.sample(system_bins, batch_size)

    print(
        f"Found {len(system_bins)} unknown/untested tools. Probing batch of {batch_size}...\n"
    )

    successful_imports = 0
    reject_terms = [
        "usage:",
        "options:",
        "params",
        "or:",
        "[option]",
        "not found",
        "no such file",
        "command not found",
        "can't locate",
        "no module named",
        "traceback",
        "exception",
    ]

    def scan_worker(cmd):
        full_path = None
        for path_dir in path_dirs:
            if path_dir in allowed_paths:
                candidate = os.path.join(path_dir, cmd)
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    full_path = candidate
                    break
        if not full_path:
            return cmd, None

        # Layer 1: OS Query
        try:
            process = subprocess.run(
                ["whatis", cmd],
                capture_output=True,
                text=True,
                errors="replace",
                check=True,
            )
            desc = process.stdout.strip()
            return cmd, {
                "desc": sanitize_text(desc),
                "example": f"{cmd} --help",
                "category": "Auto-Imported Libs",
                "source": "OS Manual",
            }
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        try:
            process = subprocess.run(
                ["bash", "-c", 'help -d "$1"', "_", cmd],
                capture_output=True,
                text=True,
                errors="replace",
                check=True,
            )
            desc = process.stdout.strip()
            if desc:
                return cmd, {
                    "desc": sanitize_text(desc),
                    "example": f"{cmd} --help",
                    "category": "Auto-Imported Libs",
                    "source": "Built-in",
                }
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Layer 2: Static Analysis (Sentinel's Containment Protocol)
        try:
            with open(full_path, "rb") as f:
                header = f.read(4)

            lines = []
            if header == b"\x7fELF":
                process = subprocess.run(
                    ["strings", full_path],
                    capture_output=True,
                    text=True,
                    errors="replace",
                )
                lines = [
                    line.strip() for line in process.stdout.splitlines() if line.strip()
                ]
            elif header.startswith(b"#!"):
                with open(full_path, "r", errors="replace") as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
            else:
                return cmd, None

            if not lines:
                return cmd, None

            description = "An installed program. No readable description found."
            example_str = f"{cmd} --help"
            success = False

            motif_dash = re.compile(r"(?i)^\s*" + re.escape(cmd) + r"\s+-\s+(.*)")

            for i, line in enumerate(lines):
                lower_line = line.lower()
                if (
                    "example:" in lower_line
                    or "examples:" in lower_line
                    or "usage:" in lower_line
                ):
                    for j in range(1, 4):
                        if i + j < len(lines):
                            candidate = lines[i + j].strip()
                            if (
                                candidate
                                and not candidate.startswith("-")
                                and cmd in candidate
                            ):
                                example_str = sanitize_text(candidate)
                                success = True
                                break
                if success:
                    break

            if not success:
                for line in lines:
                    if motif_dash.match(line):
                        description = motif_dash.match(line).group(1).strip()
                        success = True
                        break

            if not success:
                for line in lines:
                    lower = line.lower()
                    if (
                        cmd in lower
                        and len(line) > 15
                        and not any(r in lower for r in ["[", "---", "<"])
                    ):
                        description = line
                        success = True
                        break

            if success and len(description) < 200:
                if not any(r in description.lower() for r in reject_terms):
                    return cmd, {
                        "desc": sanitize_text(description),
                        "example": sanitize_text(example_str),
                        "category": "Auto-Imported Libs",
                        "source": "Static Analysis",
                    }
        except Exception as e:
            return cmd, {"error": str(e)}

        return cmd, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(scan_worker, scan_batch)

    for cmd, res in results:
        if res:
            if "error" in res:
                print(
                    f" {YELLOW}[~]{RESET} Skipped {cmd}: Error during scan - {res['error']}"
                )
                continue
            state_manager.pending_imports[cmd] = {
                "desc": res["desc"],
                "example": res["example"],
                "category": res["category"],
            }
            print(
                f" {GREEN}[+]{RESET} Added to pending ({res['source']}): {CYAN}{cmd}{RESET}"
            )
            successful_imports += 1
        else:
            state_manager.probe_blacklist.append(cmd)
            print(
                f" {RED}[-]{RESET} Added to blacklist (No info found): {RED}{cmd}{RESET}"
            )

    if successful_imports > 0:
        state_manager.save_pending()
        print(
            f"\n{GREEN}Scan Complete! Found {successful_imports} new potential commands.{RESET}"
        )
    else:
        print(
            f"\n{YELLOW}Scan Complete! No usable descriptions found. (Added to blacklist){RESET}"
        )

    state_manager.save_blacklist()
    pause()
