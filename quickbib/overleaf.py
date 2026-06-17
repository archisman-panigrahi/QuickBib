"""Read an Overleaf project's source files through Overleaf's Git bridge.

Overleaf exposes every project as a Git repository. "Connecting to Overleaf"
is therefore nothing more than ``git clone`` with a personal Git token - no
plugin or external service is involved. This module wraps that so the verifier
can pull ``.bib`` / ``.tex`` files straight from a live project.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path

OVERLEAF_GIT_HOST = "git.overleaf.com"

_PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9]+$")


class OverleafError(Exception):
    """Raised when cloning/pulling an Overleaf project fails."""


def mask_token(text: str) -> str:
    """Redact a Git token embedded in a clone URL before showing an error."""
    return re.sub(r"https://git:[^@\s]+@", "https://git:***@", str(text))


def clone_or_pull(project_id: str, git_token: str, workdir: str | None = None) -> Path:
    """Clone (or update) an Overleaf project and return the local repo path.

    The project is cached under the system temp directory and re-pulled on
    subsequent calls, so repeated verification runs are fast.
    """
    project_id = (project_id or "").strip()
    if not _PROJECT_ID_RE.match(project_id):
        raise OverleafError(
            "Invalid Overleaf project ID. Copy it from the project URL: "
            "https://www.overleaf.com/project/<PROJECT_ID>"
        )
    if not (git_token or "").strip():
        raise OverleafError(
            "Missing Overleaf Git token. Create one under "
            "Overleaf -> Account Settings -> Git Integration."
        )

    base = Path(workdir) if workdir else Path(tempfile.gettempdir())
    repo = base / f"overleaf-{project_id}"
    url = f"https://git:{git_token.strip()}@{OVERLEAF_GIT_HOST}/{project_id}"
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}

    try:
        if (repo / ".git").is_dir():
            _git(["git", "-C", str(repo), "pull", "--ff-only"], env)
        else:
            base.mkdir(parents=True, exist_ok=True)
            _git(["git", "clone", "--depth", "1", url, str(repo)], env)
    except FileNotFoundError as exc:
        raise OverleafError("Git is not installed or not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise OverleafError("Timed out talking to Overleaf.") from exc
    except subprocess.CalledProcessError as exc:
        detail = mask_token((exc.stderr or exc.stdout or "").strip())
        raise OverleafError(f"Git failed: {detail or 'unknown error'}") from exc
    return repo


def _git(cmd: list[str], env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, env=env, capture_output=True, text=True, check=True, timeout=120
    )


def find_files(repo: Path, suffix: str) -> list[Path]:
    """Return project files with the given suffix, skipping the ``.git`` dir."""
    repo = Path(repo)
    return sorted(
        p for p in repo.rglob(f"*{suffix}")
        if ".git" not in p.parts and p.is_file()
    )


def find_bib_files(repo: Path) -> list[Path]:
    """All ``.bib`` files in the project."""
    return find_files(repo, ".bib")


def find_tex_files(repo: Path) -> list[Path]:
    """All ``.tex`` files in the project."""
    return find_files(repo, ".tex")
