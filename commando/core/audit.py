import json
import os
import shutil
import signal
import subprocess

from commando.utils.io import (
    BOLD,
    CYAN,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    pause,
)


def analyze_strace_output(output):
    kinetic_tags = set()
    if "connect(" in output or "sendto(" in output or "recvfrom(" in output:
        kinetic_tags.add("[Network Mutator]")
    if "openat(" in output or "read(" in output or "write(" in output:
        kinetic_tags.add("[File Reader/Writer]")
    if "execve(" in output or "clone(" in output or "fork(" in output:
        kinetic_tags.add("[Process Spawner]")
    return list(kinetic_tags)


def analyze_ldd_output(output):
    kinetic_tags = set()
    if "libssl" in output or "libcurl" in output:
        kinetic_tags.add("[Network Mutator]")
    if "libc" in output:
        kinetic_tags.add("[File Reader/Writer]")
    return list(kinetic_tags)


def search_command(
    base_command, state_manager, scanner_module, headless=False, audit=False
):
    session_history = state_manager.session_history
    probe_blacklist = state_manager.probe_blacklist
    all_known = state_manager.get_all_known_commands()

    if not headless:
        val = session_history.get(base_command, 0) + 1
        if base_command in session_history:
            session_history.pop(base_command)
        session_history[base_command] = val
        state_manager.save_history()

    if base_command in all_known:
        data = all_known[base_command]

        if audit:
            if not headless:
                print(f"\n{MAGENTA}★ Kinetic Audit for '{base_command}' ★{RESET}\n")
                print(f"{YELLOW}Running behavioral analysis via strace...{RESET}")

            # Sentinel fix: Kinetic Audit Paradox
            execute_strace = True
            strace_args = [
                "strace",
                "-f",
                "-e",
                "trace=network,file,process",
                base_command,
            ]

            if base_command in state_manager.custom_guide:
                if headless:
                    # In headless mode, never assume execution consent for custom imports
                    execute_strace = False
                else:
                    try:
                        ans = input(
                            f"{YELLOW}Warning: '{base_command}' is a custom import. Append '--help' for kinetic audit? (y/N): {RESET}"
                        ).strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        ans = "n"

                    if ans == "y":
                        strace_args.append("--help")
                    else:
                        execute_strace = False
            else:
                strace_args.append("--help")

            # BOOM fix: process group obliteration with fallback
            if not execute_strace:
                # Force fallback to static ldd
                raise FileNotFoundError("Audit aborted by user or headless constraint.")

            try:
                proc = subprocess.Popen(
                    strace_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid,
                )

                try:
                    stdout, stderr = proc.communicate(timeout=2)
                    output = stderr
                    method = "strace"
                    tags = analyze_strace_output(output)
                except subprocess.TimeoutExpired:
                    # Timeout: Try killing process group
                    try:
                        if hasattr(os, "killpg") and hasattr(os, "getpgid"):
                            # Bolt fix: Process Group Fratricide lock
                            if os.getpgid(proc.pid) != os.getpgrp():
                                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                            else:
                                proc.kill()
                        else:
                            proc.kill()
                    except (PermissionError, ProcessLookupError):
                        # Fallback: Android/SELinux doesn't allow setsid sometimes.
                        try:
                            proc.kill()
                        except OSError:
                            pass

                    # Reap the process to avoid zombie processes and close pipes
                    try:
                        proc.communicate()
                    except Exception:
                        pass

                    if headless:
                        print(
                            json.dumps(
                                {
                                    "command": base_command,
                                    "status": "[Telemetry Failed]",
                                    "kinetic_tags": [],
                                    "audit_method": "strace",
                                }
                            )
                        )
                        return
                    print(f"{RED}Error:{RESET} Program timed out and was killed.")
                    return

            except (FileNotFoundError, Exception):
                # Fallback to static ldd
                full_path = shutil.which(base_command)
                if not full_path:
                    if headless:
                        print(
                            json.dumps(
                                {
                                    "command": base_command,
                                    "status": "[Telemetry Failed]",
                                    "kinetic_tags": [],
                                    "audit_method": "static",
                                }
                            )
                        )
                        return
                    print(f"{RED}Error:{RESET} Command not found for static analysis.")
                    return

                try:
                    proc = subprocess.run(
                        ["ldd", full_path], capture_output=True, text=True, check=True
                    )
                    tags = analyze_ldd_output(proc.stdout)
                    method = "ldd"
                except Exception:
                    tags = []
                    method = "static"

            if headless:
                print(
                    json.dumps(
                        {
                            "command": base_command,
                            "status": "success",
                            "kinetic_tags": tags,
                            "audit_method": method,
                        }
                    )
                )
                return

            print(f"{CYAN}Audit Method:{RESET} {method}")
            print(
                f"{CYAN}Behavioral Tags:{RESET} {', '.join(tags) if tags else 'None detected'}"
            )
            pause()
            return

        if headless:
            print(
                json.dumps(
                    {
                        "command": base_command,
                        "status": "success",
                        "kinetic_tags": [],
                        "audit_method": "none",
                    }
                )
            )
            return

        print(f"\n{CYAN}{BOLD}Command:{RESET} {base_command}")
        print(f"{GREEN}Category:{RESET} {data.get('category', 'Custom')}")
        print(f"{YELLOW}Explanation:{RESET} {data['desc']}")
        if "example" in data:
            print(f"{MAGENTA}Example:{RESET} {data['example']}")
        print()
        pause()
        return

    if base_command in probe_blacklist:
        if headless:
            print(
                json.dumps(
                    {
                        "command": base_command,
                        "status": "blacklisted",
                        "kinetic_tags": [],
                        "audit_method": "none",
                    }
                )
            )
            return
        print(
            f"{RED}Error:{RESET} '{base_command}' is in the blacklist. Run factory reset to clear."
        )
        pause()
        return

    if headless:
        print(
            json.dumps(
                {
                    "command": base_command,
                    "status": "not_found",
                    "kinetic_tags": [],
                    "audit_method": "none",
                }
            )
        )
        return

    print(f"{RED}Error:{RESET} Couldn't find exact command '{base_command}'.")

    intent_results = scanner_module.search_intent(base_command, state_manager)
    if intent_results:
        print(f"\n{CYAN}Intent Search:{RESET} Did you mean one of these?")
        for r in intent_results:
            data = all_known[r]
            print(f" - {GREEN}{r}{RESET}: {data['desc']}")
        print()
    else:
        suggestion = scanner_module.suggest_command(base_command, state_manager)
        if suggestion:
            print(
                f"{YELLOW}Linting Suggestion:{RESET} Did you mean '{BOLD}{GREEN}{suggestion}{RESET}'?"
            )

    if session_history and list(session_history.keys())[-1] == base_command:
        del session_history[base_command]
        state_manager.save_history()
    pause()
