#!/usr/bin/env python3
"""Validate a local kirQQn brand checkout against GitHub before any AI edit.

Non-destructive: fetches remote refs but does not pull/merge or touch the worktree.
"""
import argparse
import pathlib
import subprocess
import sys

CORE = [
    "AI_INSTRUCTIONS.md",
    "AGENTS.md",
    "guidelines/КРЕАТИВНИЙ_ПЛЕЙБУК.md",
    "guidelines/ЯК_МОНТУВАТИ_В_RESOLVE.md",
    "guidelines/ЯКІСТЬ_МОНТАЖУ.md",
    "guidelines/ГАЙДЛАЙН_ЕПІЗОДИ.md",
]
ASSETS = [
    "assets/intro_outro",
    "assets/logo_emotions_avatars",
    "assets/sound_source",
    "resolve_pack",
    "constructors/kirqqn_episode",
    "templates/resolve_render_presets",
]


def run(*args, cwd):
    p = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand-dir", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.brand_dir.resolve()
    try:
        if run("rev-parse", "--show-toplevel", cwd=root) != str(root):
            raise RuntimeError("Brand directory must be the root of its own Git clone")
        remote = run("remote", "get-url", "origin", cwd=root)
        if not (remote.rstrip("/").removesuffix(".git").endswith("Kirqqn/kirQQn-brand")):
            raise RuntimeError("origin is not Kirqqn/kirQQn-brand: " + remote)
        run("fetch", "origin", "main", cwd=root)
        head = run("rev-parse", "HEAD", cwd=root)
        latest = run("rev-parse", "refs/remotes/origin/main", cwd=root)
        if head != latest:
            raise RuntimeError(
                f"Local commit {head[:12]} != origin/main {latest[:12]}. "
                "Update with 'git pull --ff-only origin main' if safe, then re-run."
            )
        missing = [p for p in CORE + ASSETS if not (root / p).exists()]
        if missing:
            raise RuntimeError("Required brand paths missing: " + ", ".join(missing))
        print(f"kirQQn brand preflight OK | {root} | origin/main {latest}")
        print("Next: READ AI_INSTRUCTIONS.md and all editing guidelines in AGENTS.md before each edit.")
    except (RuntimeError, OSError) as e:
        print(f"kirQQn brand preflight BLOCKED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
