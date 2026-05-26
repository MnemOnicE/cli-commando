# ADR 0001: Zero-Trust Containment Protocol for Unknown Binaries

## Status
Accepted

## Context
CLI-Commando operates as a system scanner that discovers unknown and undocumented executables in the user's `PATH`. The initial prototype attempted to execute these unknown binaries with common flags like `--help` to extract usage information.

However, in an untrusted environment, blindly executing an unknown binary can lead to unintended side effects, privilege escalation, or malicious execution before it even attempts to parse flags. Given the tool's goal of mapping the terminal landscape without causing harm, a reactive execution strategy is a massive security liability.

## Decision
We adopt a **Zero-Trust Containment Protocol** for all newly discovered binaries. The system must default to static analysis and safe, controlled queries. Arbitrary execution of unknown binaries (e.g., via `subprocess.run` with common flags) is strictly prohibited.

The containment protocol enforces the following bifurcated check without execution:
1. **OS Query Validation**: The system first attempts to identify the binary through standard, known-safe OS interfaces like `whatis` or built-in `bash help`.
2. **Header Identification**: Read the first 4 bytes of the unknown file to securely determine its type.
3. **Static Extraction (ELF)**: If the binary is a compiled ELF executable (magic number `\x7fELF`), pipe it through `strings` to extract text blocks and usage motifs. The file is never executed.
4. **Static Extraction (Scripts)**: If it hits a shebang (`#!`), read the file as raw text to parse comments and variables.

For behavioral profiling (kinetic auditing), `strace` is used when permitted. If the kernel denies `ptrace` (e.g., in strict SELinux environments or Termux), the system gracefully degrades to static library analysis using `ldd`, inferring behavior from linked libraries (e.g., `libssl` implies network mutator) without running the file.

## Consequences
- **Positive**: We completely eliminate the risk of executing a malicious payload during the auto-scan phase.
- **Positive**: We increase the reliability of the scanner in restricted environments like Termux on unrooted Android devices.
- **Negative**: The accuracy of descriptions extracted via `strings` is often lower than querying `--help` directly, requiring more sophisticated text parsing heuristics to find the "usage" blocks among the raw string output.
- **Negative**: Adds a dependency on coreutils like `strings` and `ldd`, though these are nearly ubiquitous in POSIX environments.
