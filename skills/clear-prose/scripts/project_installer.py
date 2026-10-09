#!/usr/bin/env python3
"""project_installer.py - Installs prose tools into existing or new repositories.

Provides:
- init_new_project: Scaffolds a new Git + Bazel project with AGENTS.md, githooks, and clear-prose skill.
- install_to_project: Safely integrates with an existing project without overwriting files.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent
if (SELF_DIR / "sw_rules.json").exists():
    ROOT = SELF_DIR.parent
    SKILL_SRC = SELF_DIR.parent
    TEMPLATES_DIR = SKILL_SRC / "templates"
else:
    ROOT = SELF_DIR.parent
    TEMPLATES_DIR = ROOT / "templates"
    SKILL_SRC = ROOT / "skills" / "clear-prose"

PROSE_RULES_SNIPPET = """

## Prose Style Guidelines

All project documentation, specifications, and code comments must adhere to clear prose standards.

### 1. Specifications and Task Files (ASD-STE100)
For files in `specs/`, `tasks/`, `verification/`, and code comments:
- Follow Simplified Technical English (ASD-STE100).
- Keep procedural sentences to a maximum of 20 words.
- Keep descriptive sentences to a maximum of 25 words.
- Use active voice only.
- Do not use contractions or Latin abbreviations (`e.g.`, `i.e.`, `etc.`).

### 2. General Documentation and Guides (Strunk & White)
For files in `docs/`, `proposals/`, and `README.md`:
- Follow Strunk & White (*The Elements of Style*).
- Omit needless words.
- Use the active voice.
- Put statements in positive form.
- Use the serial (Oxford) comma in lists of three or more terms.
- Avoid overused qualifiers (`very`, `rather`, `little`, `pretty`).

### 3. Git Commit Messages
- Keep subject lines to a maximum of 50 characters.
- Capitalize the subject line.
- Do not end the subject line with a period.
- Put one blank line between the subject and the body.
- Wrap body lines at 72 characters.
- Use imperative mood in the subject ("Add feature", not "Added feature").
- Apply ASD-STE100 to the commit body text.
"""

BAZEL_BUILD_SNIPPET = """

# Clear-prose test target
sh_test(
    name = "prose_lint_test",
    size = "small",
    srcs = ["@clear_prose_linter//:prose_lint_test.sh"],
    data = [
        "//:docs",
    ],
)
"""


def setup_git_hooks(target_dir: Path) -> list[str]:
    """Installs commit-msg and pre-commit hooks safely."""
    actions: list[str] = []
    hook_dir_name = ".githooks" if (target_dir / ".githooks").is_dir() else "githooks"
    githooks_dir = target_dir / hook_dir_name
    githooks_dir.mkdir(parents=True, exist_ok=True)

    for hook_name in ("commit-msg", "pre-commit"):
        src = TEMPLATES_DIR / "githooks" / hook_name
        dest = githooks_dir / hook_name
        if not dest.exists():
            shutil.copy2(src, dest)
            dest.chmod(0o755)
            actions.append(f"Created hook {dest.relative_to(target_dir)}")
        else:
            actions.append(f"Preserved existing hook {dest.relative_to(target_dir)}")

    # Configure core.hooksPath if inside a git repository
    if (target_dir / ".git").exists():
        subprocess.run(
            ["git", "config", "core.hooksPath", hook_dir_name],
            cwd=target_dir,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        actions.append(f"Configured git core.hooksPath = {hook_dir_name}")

    return actions


def setup_agents_rule(target_dir: Path) -> list[str]:
    """Sets up or updates AGENTS.md."""
    actions: list[str] = []
    agents_file = target_dir / "AGENTS.md"

    if not agents_file.exists():
        template = TEMPLATES_DIR / "AGENTS.md.template"
        shutil.copy2(template, agents_file)
        actions.append("Created AGENTS.md with prose style guidelines")
    else:
        content = agents_file.read_text(encoding="utf-8")
        if "Prose Style Guidelines" not in content:
            with open(agents_file, "a", encoding="utf-8") as f:
                f.write(PROSE_RULES_SNIPPET)
            actions.append("Appended Prose Style Guidelines to existing AGENTS.md")
        else:
            actions.append("AGENTS.md already contains prose guidelines")

    return actions


def setup_skill(target_dir: Path) -> list[str]:
    """Installs or links clear-prose skill into .agents/skills/."""
    actions: list[str] = []
    dest_skills = target_dir / ".agents" / "skills" / "clear-prose"
    dest_skills.parent.mkdir(parents=True, exist_ok=True)

    if not dest_skills.exists():
        if SKILL_SRC.exists():
            shutil.copytree(SKILL_SRC, dest_skills)
            actions.append(f"Installed clear-prose skill to {dest_skills.relative_to(target_dir)}")
    else:
        actions.append(f"Skill already present at {dest_skills.relative_to(target_dir)}")

    return actions


def setup_bazel_rules(target_dir: Path) -> list[str]:
    """Adds Bazel test snippet if BUILD.bazel exists."""
    actions: list[str] = []
    build_bazel = target_dir / "BUILD.bazel"
    if build_bazel.exists():
        content = build_bazel.read_text(encoding="utf-8")
        if "prose_lint_test" not in content:
            with open(build_bazel, "a", encoding="utf-8") as f:
                f.write(BAZEL_BUILD_SNIPPET)
            actions.append("Appended prose_lint_test target to BUILD.bazel")
        else:
            actions.append("BUILD.bazel already defines prose_lint_test")
    return actions


def install_to_project(target_path: str | Path, skip_bazel: bool = False) -> list[str]:
    """Installs prose linting, hooks, and guidelines into an existing project."""
    target_dir = Path(target_path).resolve()
    if not target_dir.is_dir():
        raise NotADirectoryError(f"{target_dir} is not a directory")

    actions: list[str] = []
    actions.extend(setup_git_hooks(target_dir))
    actions.extend(setup_agents_rule(target_dir))
    actions.extend(setup_skill(target_dir))
    if not skip_bazel:
        actions.extend(setup_bazel_rules(target_dir))

    # Copy prose_lint.py into project utils/ or scripts/
    script_dir_name = "utils" if (target_dir / "utils").is_dir() else "scripts"
    linter_dest = target_dir / script_dir_name / "prose_lint.py"
    linter_dest.parent.mkdir(parents=True, exist_ok=True)
    linter_src = ROOT / "prose_lint.py"
    if linter_src.exists() and not linter_dest.exists():
        shutil.copy2(linter_src, linter_dest)
        linter_dest.chmod(0o755)
        actions.append(f"Copied prose_lint.py to {linter_dest.relative_to(target_dir)}")

    # Copy reflow_commit.py as well
    reflow_src = ROOT / "scripts" / "reflow_commit.py"
    reflow_dest = target_dir / script_dir_name / "reflow_commit.py"
    if reflow_src.exists() and not reflow_dest.exists():
        shutil.copy2(reflow_src, reflow_dest)
        reflow_dest.chmod(0o755)
        actions.append(f"Copied reflow_commit.py to {reflow_dest.relative_to(target_dir)}")

    return actions


def init_new_project(target_path: str | Path) -> list[str]:
    """Scaffolds a new Git + Bazel project with prose guidelines."""
    target_dir = Path(target_path).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    actions: list[str] = []

    # Initialize Git
    if not (target_dir / ".git").exists():
        subprocess.run(["git", "init", "-b", "main"], cwd=target_dir, check=True, stdout=subprocess.DEVNULL)
        actions.append("Initialized git repository")

    # Standard git files
    gitignore = target_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("bazel-*\n__pycache__/\n*.pyc\n.pytest_cache/\n", encoding="utf-8")
        actions.append("Created .gitignore")

    editorconfig = target_dir / ".editorconfig"
    if not editorconfig.exists():
        editorconfig.write_text("root = true\n\n[*]\nend_of_line = lf\ninsert_final_newline = true\ntrim_trailing_whitespace = true\n\n[*.md]\nmax_line_length = 72\n", encoding="utf-8")
        actions.append("Created .editorconfig")

    # Bazel scaffolding
    module_bazel = target_dir / "MODULE.bazel"
    if not module_bazel.exists():
        module_name = target_dir.name.replace("-", "_").lower()
        module_bazel.write_text(f'module(\n    name = "{module_name}",\n    version = "0.1.0",\n)\n', encoding="utf-8")
        actions.append("Created MODULE.bazel")

    build_bazel = target_dir / "BUILD.bazel"
    if not build_bazel.exists():
        build_bazel.write_text('load("@rules_python//python:defs.bzl", "py_binary")\n\nexports_files(["README.md"])\n', encoding="utf-8")
        actions.append("Created BUILD.bazel")

    actions.extend(setup_git_hooks(target_dir))
    actions.extend(setup_agents_rule(target_dir))
    actions.extend(setup_skill(target_dir))

    return actions


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("init", "install"):
        print("Usage: project_installer.py [init|install] [--no-bazel] <target_directory>")
        sys.exit(1)

    cmd = sys.argv[1]
    skip_bazel = "--no-bazel" in sys.argv
    remaining = [a for a in sys.argv[2:] if a != "--no-bazel"]
    tgt = remaining[0] if remaining else "."
    results = init_new_project(tgt) if cmd == "init" else install_to_project(tgt, skip_bazel=skip_bazel)
    print(f"Project {cmd} finished in {tgt}:")
    for a in results:
        print(f"  - {a}")
