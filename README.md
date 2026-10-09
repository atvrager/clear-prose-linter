# Clear Prose Linter and Skill

Clear Prose is a unified writing linter and Antigravity skill.
It fuses two writing styles:
1. **ASD-STE100 (Simplified Technical English)** for specifications, task contracts, and commit messages.
2. **Strunk & White (*The Elements of Style*)** for design documentation, proposals, and user guides.

## Provenance
- Source Book: *The Elements of Style*, 4th Edition
- Authors: William Strunk Jr. and E. B. White
- Archive URL: https://archive.org/details/pdfy-2_qp8jQ61OI6NHwa
- SHA-256 Checksum: `75527b11f8db39481c7b4eace61358ec5377104da151cf19b1368c1344b47996`

## Features
- **Contextual Style Routing**: Selects STE mode for tasks and specifications, and Strunk & White mode for documentation.
- **Strict Git Commit Rules**: Enforces 50-character subjects and 72-character body lines.
- **Automated Reflow Formatter**: Wraps commit message paragraphs to 72 characters while preserving lists and code blocks.
- **Project Installer**: Installs git hooks, `AGENTS.md` guidelines, and skills into existing repositories.
- **Antigravity Skill**: Guides the AI agent to write clean, concise prose.
- **Bazel Integration**: Provides Bazel build rules and test targets.

## Usage

### Lint Files
```bash
python3 prose_lint.py [files...]
```

### Automatically Fix Needless Words
```bash
python3 prose_lint.py --fix [files...]
```

### Lint a Commit Message
```bash
python3 prose_lint.py --commit < commit_message.txt
```

### Reflow a Commit Message
```bash
python3 prose_lint.py --fix-commit < commit_message.txt
```

### Install into an Existing Project
```bash
python3 prose_lint.py install /path/to/project
```

### Initialize a New Project
```bash
python3 prose_lint.py init /path/to/project
```
