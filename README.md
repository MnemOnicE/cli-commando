# CLI-Commando

**CLI-Commando** is your terminal command explorer and tutor. It learns the commands you actually use, mapping the CLI landscape dynamically, and providing helpful usage examples directly when you need them.

## Features

- **Interactive Dashboard:** Tracks command usage, custom definitions, and auto-imported descriptions.
- **System Auto-Scanner:** Defensively scans your system `PATH` for unknown executables using static analysis (safely examining ELF binaries and shell scripts without arbitrary execution) to build a robust local knowledge base.
- **Kinetic Auditing:** Profiles commands dynamically using `strace` to detect system calls (e.g., tagging network mutators or file readers), with graceful degradation to `ldd` static analysis when executed in restricted environments.
- **Bash Hook Integration:** Automatically hooks into your `command_not_found_handle` in bash to provide instant commando assistance.
- **Quizzes:** Run quick quizzes to test your knowledge of your own command history.

![Demonstration of Kinetic Audit](assets/kinetic_audit_demo.gif)
![Demonstration of TUI Quiz](assets/tui_quiz_demo.gif)

## Architecture

CLI-Commando transitions from dynamic probing to secure, defensive scanning:
- It safely extracts usage text from local binaries without running them.
- It employs concurrent execution carefully throttled to preserve system performance (especially on ARM and constrained hardware).
- It is designed as a fully modular Python package.

### Data Flow Diagrams

Below are the detailed workflows that power CLI-Commando. They share a consistent color coding scheme:
* **Blue**: Core processes and actions
* **Yellow**: Logical decisions
* **Green**: Data storage and databases
* **Red**: Fallbacks, errors, or rejections

#### 1. Overall Command Search Flow
How CLI-Commando handles a standard search query from the user.

```mermaid
flowchart TD
    classDef process fill:#d4e6f1,stroke:#2874a6,stroke-width:2px,color:#1b4f72;
    classDef decision fill:#fcf3cf,stroke:#b7950b,stroke-width:2px,color:#7d6608;
    classDef database fill:#d5f5e3,stroke:#1e8449,stroke-width:2px,color:#145a32;
    classDef fallback fill:#fadbd8,stroke:#cb4335,stroke-width:2px,color:#78281f;

    User[User Searches Command] --> LogHistory[Log to History DB]:::database
    LogHistory --> KnownCheck{In Known DB?}:::decision
    KnownCheck -- Yes --> AuditCheck{Audit Flag?}:::decision
    AuditCheck -- Yes --> KineticAudit[Execute Kinetic Audit Flow]:::process
    AuditCheck -- No --> DisplayInfo[Display Description & Example]:::process
    KnownCheck -- No --> BlacklistCheck{In Blacklist?}:::decision
    BlacklistCheck -- Yes --> Block[Reject: Blacklisted]:::fallback
    BlacklistCheck -- No --> IntentSearch{Intent Matches?}:::decision
    IntentSearch -- Yes --> DisplayIntent[Display Intent Matches]:::process
    IntentSearch -- No --> Suggestion[Suggest Similar Commands]:::process
```

#### 2. System Auto-Scanner Flow
The zero-trust containment protocol for discovering and learning about new executables safely without arbitrary execution.

```mermaid
flowchart TD
    classDef process fill:#d4e6f1,stroke:#2874a6,stroke-width:2px,color:#1b4f72;
    classDef decision fill:#fcf3cf,stroke:#b7950b,stroke-width:2px,color:#7d6608;
    classDef database fill:#d5f5e3,stroke:#1e8449,stroke-width:2px,color:#145a32;
    classDef fallback fill:#fadbd8,stroke:#cb4335,stroke-width:2px,color:#78281f;

    StartScan[Scan PATH Directories] --> FilterBins[Filter Unknown Binaries]:::process
    FilterBins --> BatchLimit[Select Batch Limit]:::process
    BatchLimit --> OSManualCheck{OS Manual Exists?<br/>whatis / bash help}:::decision
    OSManualCheck -- Yes --> ParseManual[Extract Manual Text]:::process
    OSManualCheck -- No --> FileHeaderCheck{Check File Header}:::decision
    FileHeaderCheck -- ELF Binary --> StringsScan[Run 'strings' Static Analysis]:::process
    FileHeaderCheck -- Shell Script --> ReadText[Read File Text]:::process
    FileHeaderCheck -- Unknown / Other --> BlacklistAdd[Add to Blacklist DB]:::database
    StringsScan --> ParseText[Extract Description & Usage Motif]:::process
    ReadText --> ParseText
    ParseText --> SuccessCheck{Text Valid?}:::decision
    SuccessCheck -- Yes --> PendingImports[Add to Pending Imports DB]:::database
    SuccessCheck -- No --> BlacklistAdd
    ParseManual --> PendingImports
```

#### 3. Kinetic Audit Flow
The dynamic behavioral profiling system with its graceful degradation into static analysis.

```mermaid
flowchart TD
    classDef process fill:#d4e6f1,stroke:#2874a6,stroke-width:2px,color:#1b4f72;
    classDef decision fill:#fcf3cf,stroke:#b7950b,stroke-width:2px,color:#7d6608;
    classDef database fill:#d5f5e3,stroke:#1e8449,stroke-width:2px,color:#145a32;
    classDef fallback fill:#fadbd8,stroke:#cb4335,stroke-width:2px,color:#78281f;

    StartAudit[Start Audit on Known Command] --> RunStrace[Run 'strace'<br/>Timeout: 2s]:::process
    RunStrace --> StraceStatus{Execution Status}:::decision
    StraceStatus -- Success --> ParseStrace[Parse System Calls]:::process
    ParseStrace --> AssignTagsStrace[Assign Tags<br/>Network, File, Process]:::process
    StraceStatus -- Timeout / Killed --> ErrorExit[Exit with Timeout Error]:::fallback
    StraceStatus -- Startup Error / No strace --> LddFallback[Fallback to 'ldd' Static Analysis]:::fallback
    LddFallback --> LddStatus{ldd Status}:::decision
    LddStatus -- Success --> ParseLdd[Parse Shared Libraries]:::process
    ParseLdd --> AssignTagsLdd[Assign Tags<br/>libcurl, libssl, libc]:::process
    LddStatus -- Error --> StaticFallback[Fallback to Static/None]:::fallback
    StaticFallback --> Output[Format Output / JSON]:::process
    AssignTagsStrace --> Output
    AssignTagsLdd --> Output
```

## Prerequisites & Environment

While the tool is installed via `pip`, it relies on the following OS-level binaries for its core functionality:
- **Strictly Required:** `strings` (used for safe static analysis of binaries).
- **Gracefully Degraded:**
  - `strace` (used for kinetic auditing; if unavailable or blocked by `ptrace` restrictions, falls back to static analysis).
  - `ldd` (used for static analysis fallback).
  - `whatis` (used to query known-safe system interfaces for command definitions).
  - `readelf` (used to securely examine ELF headers without execution).

**Termux** is explicitly recognized as a fully supported, first-class environment.

## Installation

For standard installation:

```bash
pip install .
```

For active development (editable mode):

```bash
pip install -e .
```

*(Note: Ensure your `~/.local/bin` or equivalent Python bin directory is in your system's `$PATH` for the OS to recognize the `commando` command globally).*

## Usage

Start the interactive terminal dashboard:

```bash
commando
```

Search for a specific command immediately:

```bash
commando search <command>
```

Run a kinetic audit to see exactly what an executable does under the hood:

```bash
commando search <command> --audit
```
