# Project Installation and Setup Guide

This guide describes how to install clear-prose into existing repositories or initialize new projects.

## Installing into an Existing Repository

To install clear-prose into an existing project:

```bash
python3 prose_lint.py install /path/to/project
```

### What `install` Does:
1. **Installs Git Hooks**:
   - Creates `githooks/commit-msg` and `githooks/pre-commit`.
   - Configures `core.hooksPath` to `githooks`.
   - Preserves existing hooks without overwriting them.
2. **Updates Project Guidelines**:
   - If `AGENTS.md` exists, appends the Prose Style Guidelines section.
   - If `AGENTS.md` does not exist, creates it from the template.
3. **Installs the Antigravity Skill**:
   - Copies or links the `clear-prose` skill into `<project>/.agents/skills/clear-prose/`.
4. **Integrates with Bazel**:
   - If `BUILD.bazel` exists, adds the `prose_lint_test` target definition.

## Initializing a New Project

To create a new project from scratch with all prose guidelines pre-configured:

```bash
python3 prose_lint.py init /path/to/new-project
```

### What `init` Does:
1. Initializes Git repository (`git init -b main`).
2. Creates `.gitignore`, `.editorconfig`, `MODULE.bazel`, and `BUILD.bazel`.
3. Installs git hooks in `githooks/`.
4. Creates `AGENTS.md` with complete prose guidelines.
5. Installs the `clear-prose` skill in `.agents/skills/`.
