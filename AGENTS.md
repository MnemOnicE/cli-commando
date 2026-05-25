# CLI-Commando: System-Prompt Directives for AI Contributors

This file serves as the strict architectural blueprint for AI agents and human developers maintaining the `cli-commando` repository. The architecture has evolved from a reactive, dynamic probe to a defensive, static scanner.

# The Headless API Contract (--json)

External agents and automated tooling rely on deterministic telemetry output. When the `--json` flag is utilized, the tool must output a JSON object adhering strictly to the following schema. Do not pollute headless/JSON outputs with human-readable UI strings.

```json
{
  "command": "<string>",
  "status": "<string>",
  "kinetic_tags": ["<string>"],
  "audit_method": "<string>"
}
```

* `command`: The name of the binary or script analyzed.
* `status`: The result state (e.g., "success", "[Telemetry Failed]").
* `kinetic_tags`: Array of detected behavioral tags (e.g., "[Network Mutator]", "[File Reader/Writer]").
* `audit_method`: The analysis method used (e.g., "strace", "ldd", "static").

## 1. Project Identity & Paths

- **Identity:** The application is `cli-commando` (or `commando`). Do not use legacy names like "bashlearn".
- **State Directory:** The internal state and telemetry files (history, pending, custom) are mapped to `~/.commando`.

## 2. Concurrency & Performance

- **Subprocess Sprawl:** When processing batches of operations (like `auto_scan_system`), sequential `subprocess.run` calls will choke single-threaded execution.
- **The Constraint:** Use `concurrent.futures.ThreadPoolExecutor` for I/O-bound execution, but **you must explicitly throttle it**. Never let it default to maximum workers.
- **Rule:** Enforce a strict `max_workers=4` or `5`. This yields required concurrency for UI fluidity while respecting physical thermal and memory boundaries on constrained hardware (e.g., ARM devices).

## 3. Security & Containment Protocol

- **Execution Side-Effects:** The heuristic layer must **never** blindly invoke `[cmd, '--help']` on newly discovered binaries. Unverified executables may execute maliciously before parsing flags.
- **The Containment Protocol (Static Analysis):** Implement a bifurcated header check without execution:
  1. Read the first 4 bytes of the unknown file.
  2. If it hits the ELF magic number (`\x7fELF`), pipe it through `strings` (or read binary safely in pure Python) to extract usage motifs.
  3. If it hits a shebang (`#!`), read the file as raw text and parse the comments/variables.
  4. Only run standard OS queries (`whatis`, `help`) which are known-safe interfaces.

## 4. Kinetic Audit Fallback

- **The strace Void:** Kinetic audit mode relies on `strace` to map system calls. On non-rooted mobile environments or strictly enforced SELinux policies, `ptrace` will be denied.
- **Graceful Degradation:** Do not attempt to build manual `/proc/[pid]/syscall` polling—it causes race conditions. When the kernel denies `ptrace`, catch the exception and fall back to static library analysis using `ldd`.
  - Tag binaries linked to `libssl` or `libcurl` as `[Network Mutator]`.
  - Tag binaries with heavy `libc` usage as `[File Reader/Writer]`.

## 5. Packaging & Distribution

- **Structure:** The script is not a standalone file. It operates as a structured Python package.
- **Entry Point:** The core execution block is encapsulated in `commando/main.py` under the `cli()` function using `argparse`.
- **Builder:** The project utilizes `pyproject.toml` (not `setup.py`) to generate an executable wrapper named `commando` that points to `commando.main:cli`.
