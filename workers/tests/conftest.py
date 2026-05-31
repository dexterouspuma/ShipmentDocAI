"""Path + env setup for worker tests (local mode, no Azure)."""
import os
import sys
import pathlib

os.environ.setdefault("ENVIRONMENT", "local")

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
for p in (_REPO_ROOT, _REPO_ROOT / "workers"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
