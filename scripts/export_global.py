#!/usr/bin/env python3
"""export_global.py - Exports clear-prose skill to global user configuration."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_SRC = ROOT / "skills" / "clear-prose"
GLOBAL_SKILLS_DIR = Path.home() / ".gemini" / "config" / "skills"


def export_skill() -> None:
    if not SKILL_SRC.is_dir():
        print(f"Error: Skill source not found at {SKILL_SRC}")
        sys.exit(1)

    GLOBAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    dest = GLOBAL_SKILLS_DIR / "clear-prose"

    if dest.exists():
        print(f"Removing existing global skill at {dest}...")
        shutil.rmtree(dest)

    shutil.copytree(SKILL_SRC, dest)
    print(f"Exported clear-prose skill to {dest}")

    # Also create alias for strunk-and-white
    alias_dest = GLOBAL_SKILLS_DIR / "strunk-and-white"
    if alias_dest.exists() or alias_dest.is_symlink():
        if alias_dest.is_symlink() or alias_dest.is_file():
            alias_dest.unlink()
        else:
            shutil.rmtree(alias_dest)
    try:
        alias_dest.symlink_to("clear-prose")
        print(f"Created symlink alias at {alias_dest}")
    except OSError:
        shutil.copytree(dest, alias_dest)
        print(f"Created copy alias at {alias_dest}")

    # Verify files
    files = list(dest.rglob("*"))
    print(f"Verification: {len(files)} files/directories exported.")


if __name__ == "__main__":
    export_skill()
