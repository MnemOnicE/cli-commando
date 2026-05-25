# Security Policy

## Supported Versions
Only the latest branch/release of CLI-Commando is officially supported with security updates.

## Reporting a Vulnerability

Because `cli-commando` deals with system PATH scanning, heuristic parsing, and binary telemetry, it sits on a sensitive execution boundary. We take vulnerabilities in this boundary seriously.

If you are a security researcher and discover a vulnerability (for example, crafting a malicious ELF binary that bypasses the readelf regex and triggers arbitrary execution), please report it privately. Do not open a public GitHub issue that exposes the zero-day to everyone.

Please report any suspected vulnerabilities by emailing:

**security@commando.dev**

You should receive a response within 48 hours. If the vulnerability is accepted, we will work with you to patch and securely release the fix before public disclosure.
