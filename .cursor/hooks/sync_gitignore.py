#!/usr/bin/env python3
"""Keep .gitignore current for a conservative set of generated artifacts."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from factory_lib import emit, read_stdin_json, repo_root

ArtifactFinder = Callable[[Path], list[Path]]


def root_path(root: Path, name: str) -> list[Path]:
    path = root / name
    return [path] if path.exists() else []


def matching_directories(root: Path, name: str) -> list[Path]:
    return [path for path in root.rglob(name) if path.is_dir() and ".git" not in path.parts]


def python_bytecode(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in {".pyc", ".pyo", ".pyd"}
        and ".git" not in path.parts
    ]


MANAGED_ARTIFACTS: tuple[tuple[str, ArtifactFinder], ...] = (
    ("__pycache__/", lambda root: matching_directories(root, "__pycache__")),
    ("*.py[cod]", python_bytecode),
    (".pytest_cache/", lambda root: matching_directories(root, ".pytest_cache")),
    (".mypy_cache/", lambda root: matching_directories(root, ".mypy_cache")),
    (".ruff_cache/", lambda root: matching_directories(root, ".ruff_cache")),
    (".coverage", lambda root: root_path(root, ".coverage")),
    ("htmlcov/", lambda root: matching_directories(root, "htmlcov")),
    ("factory/log/", lambda root: root_path(root, "factory/log")),
)


def tracked_by_git(root: Path, path: Path) -> bool | None:
    """Return whether Git tracks a path, or None when Git cannot verify it."""
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, ValueError):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def existing_patterns(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def sync_gitignore(root: Path) -> list[str]:
    """Append safe patterns for detected, untracked generated artifacts."""
    gitignore = root / ".gitignore"
    current = existing_patterns(gitignore)
    additions: list[str] = []

    for pattern, find_artifacts in MANAGED_ARTIFACTS:
        if pattern in current:
            continue
        artifacts = find_artifacts(root)
        if not artifacts:
            continue
        tracked = [tracked_by_git(root, artifact) for artifact in artifacts]
        if any(state is None or state for state in tracked):
            continue
        additions.append(pattern)

    if additions:
        prefix = "" if not gitignore.is_file() or gitignore.read_text(encoding="utf-8").endswith("\n") else "\n"
        with gitignore.open("a", encoding="utf-8") as file:
            file.write(prefix + "\n".join(additions) + "\n")
    return additions


def main() -> int:
    data = read_stdin_json()
    try:
        sync_gitignore(repo_root(data))
    except OSError:
        # This is housekeeping only; hook failures must not block normal work.
        pass
    emit({})
    return 0


if __name__ == "__main__":
    sys.exit(main())
