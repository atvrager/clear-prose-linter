---
name: clear-prose
description: >-
  Use this skill to review, lint, format, or write prose and git commit messages
  according to Strunk & White and ASD-STE100.
---

# Clear Prose: Unified Writing and Linting Skill

This skill guides the agent to write, review, and format documentation, specifications, and git commit messages.
It fuses two writing styles:
1. **ASD-STE100 (Simplified Technical English)** for technical specifications, task contracts, and hardware descriptions.
2. **Strunk & White (*The Elements of Style*)** for architectural documentation, user guides, and general prose.

## Procedures

### 1. Identify Target Context
Before writing or reviewing text, determine the target style:
- **Use ASD-STE100 Mode** for files in `specs/`, `tasks/`, `verification/`, and code comments.
  - Keep sentences to 20 words maximum (procedural) or 25 words maximum (descriptive).
  - Use active voice only.
  - Never use contractions or Latin abbreviations (`e.g.`, `etc.`).
- **Use Strunk & White Mode** for files in `docs/`, `proposals/`, and `README.md`.
  - Omit needless words.
  - Use the active voice.
  - Put statements in positive form.
  - Use the serial (Oxford) comma in lists of three or more terms.
  - Avoid overused qualifiers (`very`, `rather`, `little`, `pretty`).
- Read [Style Selection Matrix](./references/style_matrix.md) for full guidance.

### 2. Lint and Review Prose Files
Run `prose_lint` (available in `$PATH`) or invoke the bundled script:
```bash
prose_lint path/to/file.md
```
Fallback if not in `$PATH`:
```bash
python3 ~/.gemini/config/skills/clear-prose/scripts/prose_lint.py path/to/file.md
```

To automatically apply safe word replacements:
```bash
prose_lint --fix path/to/file.md
```

### 3. Write and Format Git Commit Messages
Always format git commit messages with these rules:
- Keep the subject line to 50 characters maximum.
- Capitalize the subject line.
- Do not end the subject line with a period.
- Leave one blank line between the subject and the body.
- Wrap all body lines at 72 characters maximum.
- Use ASD-STE100 rules for the commit body text.

To automatically reflow and format a commit message:
```bash
prose_lint --fix-commit < message.txt
```
To check a commit message:
```bash
prose_lint --commit < message.txt
```
Read [Git Commit Style Guide](./references/commit_style.md) for details.

### 4. Install into Existing Projects
To install the linter, git hooks, `AGENTS.md` guidelines, and skill into an existing repository:
```bash
prose_lint install /path/to/existing-repo
```
Read [Project Installation Guide](./references/install_guide.md) for details.

### 5. Initialize a New Project
To scaffold a new Git + Bazel project with prose guidelines pre-configured:
```bash
prose_lint init /path/to/new-project
```

## References
- [Style Matrix (STE vs S&W)](./references/style_matrix.md)
- [Strunk & White Guide](./references/strunk_and_white.md)
- [ASD-STE100 Guide](./references/ste_guide.md)
- [Git Commit Style Guide](./references/commit_style.md)
- [Project Installation Guide](./references/install_guide.md)
- [Words Commonly Misused](./references/misused_words.md)
- [Elementary Rules of Usage](./references/rules_of_usage.md)
- [Elementary Principles of Composition](./references/principles_of_composition.md)
- [An Approach to Style: 21 Reminders](./references/style_reminders.md)
