# Contributing to CLI-Commando

Thank you for your interest in contributing to CLI-Commando! To ensure the project remains secure, maintainable, and highly performant, please adhere to the following guidelines.

## Submitting Pull Requests

1. **Fork and Branch:** Fork the repository and create a new branch for your feature or bug fix.
2. **Commit Messages:** Use clear, descriptive commit messages.
3. **Tests:** All code changes must include passing tests. Ensure you run the test suite before submitting a PR.
4. **Code Style:** Maintain standard library purity wherever possible. Avoid introducing external dependencies unless absolutely necessary and approved by maintainers.

## Running Tests

CLI-Commando uses the built-in `unittest` framework. To run the test suite, use the discovery command from the root directory:

```bash
python -m unittest discover tests
```

Ensure all tests pass before opening a Pull Request.

## Zero-Trust Execution Rule

Because `cli-commando` deals with untrusted binaries across the system `PATH`, we strictly enforce the **Zero-Trust Execution Rule**:

*   **Static Analysis Default:** Any new parsing logic or heuristic must default to static analysis methods (e.g., `readelf`, `strings`, parsing headers).
*   **No Arbitrary Execution:** You must **never** blindly invoke unknown binaries (e.g., using `subprocess.run([unknown_binary])` or `subprocess.run([unknown_binary, '--help'])`).
*   **Enforcement:** Pull Requests that introduce the arbitrary execution of unverified binaries will be automatically rejected.
