#!/usr/bin/env bash
# SFFS Linux launcher — bash sffs.sh   or   chmod +x sffs.sh && ./sffs.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== SFFS - Smart File Fortify System ==="

PYTHON="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found. Install: sudo apt install python3 python3-pip"
    exit 1
fi

VERSION="$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")"
REQUIRED="3.10"
if [ "$(printf '%s\n' "$REQUIRED" "$VERSION" | sort -V | head -n1)" != "$REQUIRED" ]; then
    echo "ERROR: Python $REQUIRED+ required (found $VERSION)"
    exit 1
fi

if [ ! -f ".deps_installed" ]; then
    echo "Installing dependencies (first run)..."
    "$PYTHON" -m pip install -r main-code/requirements.txt --quiet --user
    touch .deps_installed
    echo "Dependencies installed."
fi

if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "No display — headless mode"
    "$PYTHON" main-code/main.py --headless "$@"
else
    "$PYTHON" main-code/main.py "$@"
fi
