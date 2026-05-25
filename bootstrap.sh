#!/usr/bin/env bash
set -euo pipefail

echo "==> Starting bootstrap process..."

# 1. Platform detection (Termux)
if [ -n "${TERMUX_VERSION:-}" ] || [ -d "/data/data/com.termux/files/usr" ]; then
    echo "==> Termux environment detected."
    for pkg in python clang make; do
        if ! command -v "$pkg" > /dev/null 2>&1; then
            echo "WARNING: Required system package '$pkg' is missing. Please install it using 'pkg install $pkg'."
        fi
    done
fi

# 2. Version Check: Enforce Python 3.8+
if command -v python3 > /dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python > /dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "ERROR: python3 or python command not found."
    exit 1
fi

PYTHON_MAJOR=$($PYTHON_BIN -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$($PYTHON_BIN -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo "ERROR: Python 3.8+ is required. Found Python $PYTHON_MAJOR.$PYTHON_MINOR"
    exit 1
fi

echo "==> Found Python $PYTHON_MAJOR.$PYTHON_MINOR"

# 3. Isolation: Create the virtual environment
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "==> Virtual environment 'venv' already exists. Skipping creation."
else
    echo "==> Creating virtual environment in 'venv'..."
    $PYTHON_BIN -m venv venv
fi

# 4. Activation: Source the environment
echo "==> Activating virtual environment..."
source venv/bin/activate

# 5. Core Upgrade: Update foundational build tools
echo "==> Upgrading core tools (pip, build, setuptools)..."
pip install --upgrade pip build setuptools

# 6. Injection: Perform the editable installation
echo "==> Installing project in editable mode..."
pip install -e .

# 7. Validation: Execute the test suite
echo "==> Validating installation by running tests..."
set +e
python -m unittest discover tests
TEST_STATUS=$?
set -e

if [ $TEST_STATUS -ne 0 ]; then
    echo "=========================================================================="
    echo "SEVERE WARNING: Test suite failed! The virtual environment is NOT stable."
    echo "=========================================================================="
    exit 1
fi

echo "==> Bootstrap complete! Run 'source venv/bin/activate' to start working."
