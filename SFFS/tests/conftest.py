"""Pytest configuration — ensures SFFS package roots are on sys.path."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _sub in ("code1", "code2", "code3", "main-code"):
    p = str(_ROOT / _sub)
    if p not in sys.path:
        sys.path.insert(0, p)
