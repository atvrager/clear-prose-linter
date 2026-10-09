# Git Commit Message Style Guide

This guide describes the strict rules and automated tools for git commit messages.

## Format Requirements

Every commit message must follow this structure:

```text
Capitalized subject line max 50 chars without period

Body text wrapped at 72 characters maximum. There must be exactly one
blank line separating the subject line and the body text.

* Lists are supported and will keep their indentation.
* Code blocks are preserved without word-wrapping.
```

## Rules Summary

1. **Subject Line**:
   - 50 characters maximum (hard limit).
   - Must start with a capital letter.
   - Must not end with a period.
   - Use the imperative mood ("Add feature", not "Added feature" or "Adding feature").
   - Must not contain `wip`, `fixup!`, or `squash!` prefixes.
2. **Separator**:
   - Exactly one blank line between the subject and the body.
3. **Body Lines**:
   - 72 characters maximum per line.
   - Use ASD-STE100 rules for the prose.
   - No contractions (`don't` -> `do not`).
   - No Latin abbreviations (`e.g.` -> `for example`).
   - No trailing whitespace.

## Automated Reflow Tool

You can automatically reflow any commit message to this standard:

```bash
python3 prose_lint.py --fix-commit < raw_message.txt
```

The reflow tool:
- Truncates or formats the subject to 50 characters.
- Inserts the required blank line.
- Wraps body paragraphs to 72 characters.
- Preserves markdown bullet lists, numbered lists, blockquotes, and code blocks.
- Strips trailing whitespace.
