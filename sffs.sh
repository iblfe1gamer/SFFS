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

APPARMOR_PROFILE="sffs-main-code"
if command -v aa-exec >/dev/null 2>&1; then
    if aa-status --enabled >/dev/null 2>&1; then
        export SFFS_OS_ISOLATION="apparmor"
        RUN_PREFIX=(aa-exec -p "$APPARMOR_PROFILE")
        SECURE_FLAG=(--secure-required)
        echo "AppArmor secure mode requested with profile: $APPARMOR_PROFILE"
    else
        RUN_PREFIX=()
        SECURE_FLAG=()
    fi
else
    RUN_PREFIX=()
    SECURE_FLAG=()
fi

if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "No display — headless mode"
    "${RUN_PREFIX[@]}" "$PYTHON" main-code/main.py "${SECURE_FLAG[@]}" --headless "$@"
else
    "${RUN_PREFIX[@]}" "$PYTHON" main-code/main.py "${SECURE_FLAG[@]}" "$@"
fi
