from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

def project_root(start: Optional[Path] = None) -> Path:
    """
    Walk up from `start` (or this file) until a folder containing 'core/' is found.
    """
    here = (start or Path(__file__).resolve()).resolve()
    for p in [here] + list(here.parents):
        if (p / "core").exists():
            return p
    return here.parent.parent

def _sqlite_url_for_path(p: Path) -> str:
    """
    Build a SQLAlchemy-compatible SQLite URL for an absolute filesystem path.
    - Windows: sqlite:///C:/path/to/db.sqlite
    - POSIX:   sqlite:////abs/path/to/db.sqlite
    """
    p = p.resolve()
    if os.name == "nt":
        return "sqlite:///" + str(p).replace("\\", "/")
    return "sqlite:////" + str(p)

def resolve_db_url(db_url: str) -> str:
    """
    Ensure SQLite URLs point to a single absolute DB file so all Streamlit pages share one DB.

    Accepts:
      - sqlite:///data/db/candidates.sqlite (relative to project root)
      - sqlite:///C:/abs/path/candidates.sqlite (Windows absolute)
      - sqlite:////abs/path/candidates.sqlite (POSIX absolute)

    Returns a normalized absolute SQLite URL (platform-correct), or returns non-sqlite URLs unchanged.
    """
    if not db_url:
        db_url = "sqlite:///data/db/candidates.sqlite"

    if not db_url.startswith("sqlite:"):
        return db_url

    # Case 1: relative sqlite:///...
    if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
        tail = db_url[len("sqlite:///"):]  # could be relative or Windows absolute (C:/...)
        # Windows absolute form: C:/... or C:\...
        if os.name == "nt" and (len(tail) >= 3 and tail[1] == ":" and (tail[2] == "/" or tail[2] == "\\")):
            abs_path = Path(tail.replace("/", "\\"))
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            return _sqlite_url_for_path(abs_path)

        # Otherwise treat as repo-relative
        abs_path = project_root() / tail
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        return _sqlite_url_for_path(abs_path)

    # Case 2: sqlite:////... (POSIX absolute; sometimes appears on Windows too)
    if db_url.startswith("sqlite:////"):
        tail = db_url[len("sqlite:////"):]
        if os.name == "nt":
            tail = tail.lstrip("/")  # avoid invalid \C:\... paths
            abs_path = Path(tail.replace("/", "\\"))
        else:
            abs_path = Path("/" + tail.lstrip("/"))
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        return _sqlite_url_for_path(abs_path)

    return db_url
