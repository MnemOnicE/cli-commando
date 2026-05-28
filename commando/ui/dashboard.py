import os
import random
import shutil
import sys

from commando.utils.io import (
    BLACKLIST_FILE,
    BOLD,
    CUSTOM_DICT_FILE,
    CYAN,
    DEBUG_LOG_FILE,
    GREEN,
    HISTORY_FILE,
    MAGENTA,
    PENDING_DICT_FILE,
    RED,
    RESET,
    YELLOW,
    clear_screen,
    pause,
    save_json,
)


def print_dashboard(session_history, pending_imports):
    clear_screen()
    print(f"{CYAN}{BOLD}=============================================={RESET}")
    print(f"{CYAN}{BOLD}      Terminal Command Explorer & Tutor       {RESET}")
    print(f"{CYAN}{BOLD}=============================================={RESET}")

    if session_history:
        print(
            f"{MAGENTA}Recent: {', '.join(list(session_history.keys())[-5:])}{RESET}\n"
        )

    print(f" {GREEN}[1]{RESET} Explore Random Command")
    print(f" {GREEN}[2]{RESET} Explore by Category")
    print(f" {GREEN}[3]{RESET} Manage Custom Imports")
    print(f" {MAGENTA}[4]{RESET} Auto-Scan System for Commands")
    print(f" {YELLOW}[5]{RESET} View Debug Log")
    print(f" {RED}[6]{RESET} Factory Reset (Wipe Data)")
    if pending_imports:
        print(
            f" {CYAN}[7]{RESET} Review Pending Imports ({len(pending_imports)} waiting)"
        )
    print(f" {MAGENTA}[8]{RESET} Install Bash Hook")
    print(f" {RED}[0]{RESET} Exit & Quiz Mode")
    print(f"{YELLOW}Or type a command to search (e.g., ls, nano){RESET}\n")


def view_debug_log():
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


def factory_reset(state_manager):
    clear_screen()
    print(f"{RED}★ Factory Reset ★{RESET}\n")
    print(f" {GREEN}[1]{RESET} Clear Session History")
    print(f" {GREEN}[2]{RESET} Clear Probe Blacklist")
    print(f" {GREEN}[3]{RESET} Clear Custom Imported Commands")
    print(f" {RED}[4]{RESET} NUKE ALL DATA")
    print(f" {YELLOW}[0]{RESET} Cancel")

    choice = input(f"\n{GREEN}➜ {RESET}").strip()

    if choice == "1":
        state_manager.session_history = {}
        save_json(HISTORY_FILE, state_manager.session_history)
        print(f"{YELLOW}History cleared.{RESET}")
    elif choice == "2":
        state_manager.probe_blacklist = []
        save_json(BLACKLIST_FILE, state_manager.probe_blacklist)
        print(f"{YELLOW}Blacklist cleared.{RESET}")
    elif choice == "3":
        state_manager.custom_guide = {}
        save_json(CUSTOM_DICT_FILE, state_manager.custom_guide)
        print(f"{YELLOW}Custom imports cleared.{RESET}")
    elif choice == "4":
        state_manager.session_history = {}
        state_manager.custom_guide = {}
        state_manager.probe_blacklist = []
        state_manager.pending_imports = {}
        save_json(PENDING_DICT_FILE, state_manager.pending_imports)
        save_json(HISTORY_FILE, state_manager.session_history)
        save_json(CUSTOM_DICT_FILE, state_manager.custom_guide)
        save_json(BLACKLIST_FILE, state_manager.probe_blacklist)
        if DEBUG_LOG_FILE.exists():
            DEBUG_LOG_FILE.unlink()
        print(f"{RED}All databases and logs nuked.{RESET}")

    if choice in ["1", "2", "3", "4"]:
        pause()


def explore_category(state_manager):
    all_known = state_manager.get_all_known_commands()
    categories = sorted(list(set(data["category"] for data in all_known.values())))

    clear_screen()
    print(f"{MAGENTA}★ Categories ★{RESET}\n")
    for idx, cat in enumerate(categories, 1):
        print(f" {GREEN}[{idx}]{RESET} {cat}")
    print(f" {RED}[0]{RESET} Cancel")

    try:
        choice = input(f"\nSelect a category number: {GREEN}➜ {RESET}").strip()
        if choice == "0" or not choice.isdigit():
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


def manage_imports(state_manager):
    clear_screen()
    custom_guide = state_manager.custom_guide
    if not custom_guide:
        print(f"{YELLOW}No custom commands imported yet.{RESET}")
        pause()
        return

    print(f"{MAGENTA}★ Custom Imported Libraries ★{RESET}\n")
    for cmd, data in custom_guide.items():
        short_desc = (
            (data["desc"][:60] + "...") if len(data["desc"]) > 60 else data["desc"]
        )
        print(f" • {CYAN}{BOLD}{cmd}{RESET}: {short_desc}")

    print(f"\n{YELLOW}Options:{RESET}")
    print(f" - Type a command name to {RED}DELETE{RESET} it from the database.")
    print(" - Press Enter to return to the menu.")

    choice = input(f"\n{GREEN}➜ {RESET}").strip().lower()
    if choice in custom_guide:
        del custom_guide[choice]
        save_json(CUSTOM_DICT_FILE, custom_guide)
        print(f"{YELLOW}Successfully deleted '{choice}'.{RESET}")
        pause()
    elif choice:
        print(f"{RED}Command not found in custom imports.{RESET}")
        pause()


def run_quiz(state_manager):
    session_history = state_manager.session_history
    if len(session_history) < 3:
        print(f"\n{YELLOW}Not enough history for a quiz yet. Keep exploring!{RESET}")
        return

    clear_screen()
    print(f"{MAGENTA}★ Final Exam: Quiz Mode ★{RESET}\n")

    quiz_pool = list(session_history.keys())
    all_data = state_manager.get_all_known_commands()

    valid_pool = [cmd for cmd in quiz_pool if cmd in all_data]
    if len(valid_pool) < 3:
        print(
            f"\n{YELLOW}Not enough valid known commands for a quiz yet. Keep exploring!{RESET}"
        )
        pause()
        return

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
        else:
            weights.append(1)

    try:
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
        random.shuffle(valid_pool)
        questions = valid_pool[:3]

    score = 0
    for q_cmd in questions:
        print(f"{CYAN}Question:{RESET} Which command does the following?")
        print(f'-> "{all_data[q_cmd]["desc"]}"')
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


def _accept_pending_import(cmd, data, state_manager):
    state_manager.custom_guide[cmd] = data
    if len(state_manager.custom_guide) > 1000:
        del state_manager.custom_guide[next(iter(state_manager.custom_guide))]
    save_json(CUSTOM_DICT_FILE, state_manager.custom_guide)
    del state_manager.pending_imports[cmd]
    save_json(PENDING_DICT_FILE, state_manager.pending_imports)


def review_pending_imports(state_manager):
    pending_imports = state_manager.pending_imports
    custom_guide = state_manager.custom_guide
    probe_blacklist = state_manager.probe_blacklist

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
        print(
            f"\n{YELLOW}Options:{RESET} (y) Accept | (n) Reject | (e) Edit | (q) Quit Reviewing"
        )

        while True:
            choice = input(f"{GREEN}➜ {RESET}").strip().lower()
            if choice == "y":
                _accept_pending_import(cmd, data, state_manager)
                print(f"{GREEN}Accepted {cmd}.{RESET}")
                break
            elif choice == "n":
                probe_blacklist.append(cmd)
                save_json(BLACKLIST_FILE, probe_blacklist)
                del pending_imports[cmd]
                save_json(PENDING_DICT_FILE, pending_imports)
                print(f"{RED}Rejected {cmd}.{RESET}")
                break
            elif choice == "e":
                new_desc = input(
                    f"{CYAN}Enter new explanation for '{cmd}': {RESET}"
                ).strip()
                if new_desc:
                    data["desc"] = new_desc
                    _accept_pending_import(cmd, data, custom_guide, pending_imports)
                    print(f"{GREEN}Accepted {cmd} with edited description.{RESET}")
                else:
                    print(f"{YELLOW}Edit cancelled.{RESET}")
                break
            elif choice == "q":
                return
            else:
                print(f"{RED}Invalid choice.{RESET}")

    print(f"\n{GREEN}Finished reviewing pending imports.{RESET}")
    pause()


def install_bash_hook():
    clear_screen()
    print(f"{MAGENTA}★ Install Bash Hook ★{RESET}\n")
    print("This will add a 'command_not_found_handle' to your ~/.bashrc.")
    print(
        "When you type an unknown command, it will automatically be searched in cli-commando."
    )

    choice = input(f"\n{YELLOW}Proceed? (y/n): {RESET}").strip().lower()
    if choice == "y":
        bashrc_path = os.path.expanduser("~/.bashrc")
        script_path = sys.argv[0]
        if not os.path.isabs(script_path):
            resolved = shutil.which(script_path)
            if resolved:
                script_path = resolved
        script_path = os.path.abspath(script_path)

        # Palette fix: double-dash separation
        hook_snippet = f"""
# cli-commando auto-search hook
command_not_found_handle() {{
    python3 "{script_path}" search -- "$1"
    return 127
}}
"""
        bashrc_content = ""
        try:
            with open(bashrc_path, "r") as f:
                bashrc_content = f.read()
        except FileNotFoundError:
            pass

        # Excise old hook entirely
        if "# cli-commando auto-search hook" in bashrc_content:
            import re

            pattern = re.compile(
                r"\n?# cli-commando auto-search hook\ncommand_not_found_handle\(\) \{.*?\}\n?",
                re.DOTALL,
            )
            bashrc_content = pattern.sub("\n", bashrc_content)

        real_bashrc_path = os.path.realpath(bashrc_path)
        temp_bashrc = real_bashrc_path + ".tmp"
        try:
            with open(temp_bashrc, "w") as f:
                f.write(bashrc_content.strip() + "\n" + hook_snippet)
            os.replace(temp_bashrc, real_bashrc_path)
        except Exception:
            if os.path.exists(temp_bashrc):
                try:
                    os.remove(temp_bashrc)
                except OSError:
                    pass
            raise

        print(f"\n{GREEN}Successfully updated hook in ~/.bashrc.{RESET}")
        print(
            "Please run 'source ~/.bashrc' or restart your terminal for it to take effect."
        )
    pause()


def main_loop(state_manager, search_command_fn, auto_scan_fn):
    while True:
        session_history = state_manager.session_history
        pending_imports = state_manager.pending_imports
        all_known = state_manager.get_all_known_commands()

        print_dashboard(session_history, pending_imports)
        try:
            raw_input = input(f"{GREEN}➜ {RESET}").strip()
        except KeyboardInterrupt:
            clear_screen()
            print(f"{YELLOW}Terminating... Happy coding!{RESET}\n")
            sys.exit(0)

        if not raw_input:
            continue

        if raw_input == "1":
            cmd = random.choice(list(all_known.keys()))
            search_command_fn(cmd)
            continue
        elif raw_input == "2":
            explore_category(state_manager)
            continue
        elif raw_input == "3":
            manage_imports(state_manager)
            continue
        elif raw_input == "4":
            auto_scan_fn(state_manager)
            continue
        elif raw_input == "5":
            view_debug_log()
            continue
        elif raw_input == "6":
            factory_reset(state_manager)
            continue
        elif raw_input == "7" and pending_imports:
            review_pending_imports(state_manager)
            continue
        elif raw_input == "8":
            install_bash_hook()
            continue
        elif raw_input == "0" or raw_input.lower() == "done":
            choice = (
                input(
                    f"\n{YELLOW}Do you want to take a quick quiz on your history before leaving? (y/n): {RESET}"
                )
                .strip()
                .lower()
            )
            if choice == "y":
                run_quiz(state_manager)
            clear_screen()
            print(f"{YELLOW}Exiting... Happy coding!{RESET}\n")
            break

        command_tokens = raw_input.lower().split()
        search_command_fn(command_tokens[0])
