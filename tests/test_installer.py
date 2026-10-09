"""test_installer.py - Unit tests for project installer and initializer."""

import subprocess
import tempfile
from pathlib import Path

from scripts.project_installer import init_new_project, install_to_project


def test_init_new_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        actions = init_new_project(tmp_path)
        assert len(actions) > 0

        # Verify Git
        assert (tmp_path / ".git").is_dir()

        # Verify githooks
        assert (tmp_path / "githooks" / "commit-msg").is_file()
        assert (tmp_path / "githooks" / "pre-commit").is_file()

        # Verify AGENTS.md
        assert (tmp_path / "AGENTS.md").is_file()
        agents_text = (tmp_path / "AGENTS.md").read_text()
        assert "Prose Style Guidelines" in agents_text

        # Verify Bazel files
        assert (tmp_path / "MODULE.bazel").is_file()
        assert (tmp_path / "BUILD.bazel").is_file()

        # Verify Skill
        assert (tmp_path / ".agents" / "skills" / "clear-prose" / "SKILL.md").is_file()


def test_install_to_existing_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Setup existing git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
        (tmp_path / "AGENTS.md").write_text("# Existing Agents\n\nSome guidelines.\n")
        (tmp_path / "BUILD.bazel").write_text("# Existing build file\n")

        actions = install_to_project(tmp_path)
        assert len(actions) > 0

        # Verify hooks installed
        assert (tmp_path / "githooks" / "commit-msg").is_file()

        # Verify guidelines appended, not overwritten
        agents_text = (tmp_path / "AGENTS.md").read_text()
        assert "# Existing Agents" in agents_text
        assert "Prose Style Guidelines" in agents_text

        # Verify Bazel test appended
        build_text = (tmp_path / "BUILD.bazel").read_text()
        assert "# Existing build file" in build_text
        assert "prose_lint_test" in build_text

        # Verify Skill installed
        assert (tmp_path / ".agents" / "skills" / "clear-prose" / "SKILL.md").is_file()
