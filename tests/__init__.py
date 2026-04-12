"""
SFFS test suite.

Run all: pytest tests/ -v
One file: pytest tests/test_student1.py -v
One test: pytest tests/test_student1.py::test_decrypt_restores_original -v
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _sub in ("code1", "code2", "code3"):
    p = str(_ROOT / _sub)
    if p not in sys.path:
        sys.path.insert(0, p)
