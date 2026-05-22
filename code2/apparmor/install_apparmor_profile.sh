#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_SRC="$SCRIPT_DIR/sffs-main-code.apparmor"
PROFILE_DST="/etc/apparmor.d/sffs-main-code"

if [[ ! -f "$PROFILE_SRC" ]]; then
  echo "Profile source not found: $PROFILE_SRC" >&2
  exit 1
fi

echo "Installing AppArmor profile to $PROFILE_DST"
sudo cp "$PROFILE_SRC" "$PROFILE_DST"
sudo apparmor_parser -r "$PROFILE_DST"
echo "Profile loaded."
echo "You can verify with: sudo aa-status | rg sffs-main-code"
