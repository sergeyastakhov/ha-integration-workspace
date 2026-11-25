"""Publish a component of this workspace to its own GitHub repository.

    python tools/publish.py list
    python tools/publish.py ha-mtdx62 --message "Add the live check checklist" --dry-run
    python tools/publish.py ha-mtdx62 --message "Add the live check checklist"

A workspace folder is the source of truth while a component is being developed; the
repository is what users install. This script mirrors a folder into a clone of its
repository and pushes one ordinary commit, so published history is never rewritten.

Components are discovered, not listed: every `integrations/<domain>` becomes
`ha-<domain>`, every `libraries/<name>` becomes `<name>`. A folder without a
`custom_components/<domain>/manifest.json` is skipped, and so is a library without
`pyproject.toml` — a half-created component is not something to publish.

The clone lives in `.scratch/repos/<repo>`. The first run clones, later runs
fast-forward. A commit made locally but never pushed is pushed by the next run
instead of being reported as "nothing to publish".
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = os.environ.get("GITHUB_OWNER", "sergeyastakhov")
CLONES = ROOT / ".scratch" / "repos"
AUTHOR_NAME = os.environ.get("GIT_AUTHOR_NAME", "Sergey Astakhov")
AUTHOR_EMAIL = os.environ.get("GIT_AUTHOR_EMAIL", "sergeyastakhov@mail.ru")

SKIP_DIRS = {
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "htmlcov",
    "dist",
    "build",
}
SKIP_FILES = {".coverage"}


def discover() -> dict[str, Path]:
    """Map a repository name to the workspace folder that fills it."""
    found: dict[str, Path] = {}
    for folder in sorted((ROOT / "integrations").glob("*")):
        manifest = folder / "custom_components" / folder.name / "manifest.json"
        if manifest.exists():
            found[f"ha-{folder.name}"] = folder
    for folder in sorted((ROOT / "libraries").glob("*")):
        if (folder / "pyproject.toml").exists():
            found[folder.name] = folder
    return found


def git(cwd: Path, *args: str, secret: str | None = None) -> str:
    """Run git with secrets out of the command line."""
    env = os.environ.copy()
    config: list[tuple[str, str]] = []
    if secret:
        encoded = base64.b64encode(f"x-access-token:{secret}".encode()).decode()
        config.append(("http.extraHeader", f"Authorization: Basic {encoded}"))
    env["GIT_CONFIG_COUNT"] = str(len(config))
    for index, (key, value) in enumerate(config):
        env[f"GIT_CONFIG_KEY_{index}"] = key
        env[f"GIT_CONFIG_VALUE_{index}"] = value

    result = subprocess.run(  # fixed arguments, no shell
        ["git", *args], check=False, cwd=cwd, capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        raise SystemExit(f"git {args[0]} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def remove(target: Path) -> None:
    """Delete a tree even when git left its objects read-only."""

    def clear_readonly(function: object, path: str, _: object) -> None:
        Path(path).chmod(0o644)
        function(path)  # type: ignore[operator]

    shutil.rmtree(target, onexc=clear_readonly)


def mirror(source: Path, target: Path) -> None:
    """Make the checkout's working tree identical to the source folder."""
    for entry in target.iterdir():
        if entry.name == ".git":
            continue
        if entry.is_dir() and not entry.is_symlink():
            remove(entry)
        else:
            entry.unlink()

    def ignore(directory: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name in SKIP_DIRS or name in SKIP_FILES or name.endswith(".egg-info")
        }

    shutil.copytree(source, target, dirs_exist_ok=True, ignore=ignore)


def has_remote_branch(checkout: Path) -> bool:
    """Whether the clone knows about the branch it publishes to."""
    result = subprocess.run(  # fixed arguments, no shell
        ["git", "rev-parse", "--verify", "--quiet", "origin/main"],
        check=False,
        cwd=checkout,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def version_of(source: Path) -> str:
    """The version the component declares, for the summary line."""
    manifest = source / "custom_components" / source.name / "manifest.json"
    if manifest.exists():
        return json.loads(manifest.read_text(encoding="utf-8")).get("version", "?")
    pyproject = source / "pyproject.toml"
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.split("=", 1)[1].strip().strip('"')
    return "?"


def main() -> int:
    """Clone or fast-forward, mirror the files, commit and push."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("repo", nargs="?", help="repository name, or 'list'")
    parser.add_argument("--message", help="commit message, imperative mood")
    parser.add_argument(
        "--dry-run", action="store_true", help="mirror and show the diff only"
    )
    args = parser.parse_args()

    sources = discover()
    if args.repo in (None, "list"):
        for repo, folder in sources.items():
            print(f"{repo:32} {version_of(folder):10} {folder.relative_to(ROOT)}")
        return 0
    if args.repo not in sources:
        raise SystemExit(f"unknown repository {args.repo}; known: {', '.join(sources)}")
    if not args.message:
        raise SystemExit("--message is required to publish")

    source = sources[args.repo]
    checkout = CLONES / args.repo
    url = f"https://github.com/{OWNER}/{args.repo}.git"

    if checkout.exists():
        print(f"updating {checkout}")
        git(checkout, "pull", "--ff-only", "--quiet")
    else:
        checkout.parent.mkdir(parents=True, exist_ok=True)
        print(f"cloning {url}")
        git(CLONES, "clone", "--quiet", url, str(checkout))

    mirror(source, checkout)
    status = git(checkout, "status", "--short")
    ahead = (
        git(checkout, "log", "--oneline", "origin/main..HEAD")
        if has_remote_branch(checkout)
        else ""
    )
    if not status and not ahead:
        print("nothing to publish; the repository already matches")
        return 0
    if status:
        print(status)
    if ahead:
        print(f"{len(ahead.splitlines())} commit(s) already made here but not pushed")
    if args.dry_run:
        print("\ndry run: nothing committed")
        return 0

    if status:
        git(checkout, "add", "-A")
        git(
            checkout,
            "-c",
            f"user.name={AUTHOR_NAME}",
            "-c",
            f"user.email={AUTHOR_EMAIL}",
            "commit",
            "-q",
            "-m",
            args.message,
        )
    secret = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not secret:
        print("\ncommitted locally; set GITHUB_TOKEN to push")
        return 2
    git(checkout, "push", "origin", "HEAD:main", secret=secret)
    print("pushed:", git(checkout, "log", "--format=%h %s", "-1"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
