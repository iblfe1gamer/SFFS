#!/usr/bin/env bash
# Run or double-click (if your file manager runs scripts): starts SFFS (login window + dashboard).
# Uses the project venv if present, otherwise python3/python on PATH.
#   chmod +x RUN_SFFS.sh && ./RUN_SFFS.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PY="$SCRIPT_DIR/.venv/bin/python"
else
    PY="$(command -v python3 || command -v python || true)"
fi

if [ -z "$PY" ]; then
    echo
    echo "Python not found. Install Python 3.10 or newer (e.g. sudo apt install python3)."
    echo
    exit 1
fi

if ! "$PY" -c "import sys; assert sys.version_info >= (3,10)" 2>/dev/null; then
    echo
    echo "Python 3.10 or newer is required."
    echo "Install from https://www.python.org/downloads/"
    echo
    exit 1
fi

echo "Starting SFFS..."
"$PY" "$SCRIPT_DIR/main-code/main.py"
exitcode=$?
if [ "$exitcode" -ne 0 ]; then
    echo
    echo "SFFS exited with an error."
    if [ -t 0 ]; then
        read -r -p "Press Enter to continue..."
    fi
    exit "$exitcode"
fi
