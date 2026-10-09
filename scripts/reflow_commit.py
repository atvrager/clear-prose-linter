#!/usr/bin/env python3
"""reflow_commit.py - Formats and reflows git commit messages.

Enforces:
- Subject line max 50 characters.
- One blank line between subject and body.
- Body lines max 72 characters.
- Preserves bullet lists, code blocks, and blockquotes.
- Removes trailing whitespace.
"""

from __future__ import annotations

import re
import textwrap
from typing import NamedTuple


class ReflowResult(NamedTuple):
    text: str
    subject_warning: str | None
    changed: bool


def is_list_item(line: str) -> bool:
    """Checks if a line begins with a list marker."""
    stripped = line.lstrip()
    return bool(
        re.match(r"^([*+-]|\d+\.)\s+", stripped)
    )


def is_block_boundary(line: str) -> bool:
    """Checks if a line indicates a code block or blockquote."""
    stripped = line.lstrip()
    return stripped.startswith("```") or stripped.startswith(">") or stripped.startswith("#")


def reflow_commit_message(raw_text: str) -> ReflowResult:
    """Reflows a git commit message to 50/72 standard."""
    lines = [line.rstrip() for line in raw_text.splitlines()]
    
    # Drop leading empty lines
    while lines and not lines[0]:
        lines.pop(0)

    if not lines:
        return ReflowResult("", "empty commit message", False)

    subject = lines[0].strip()
    subject_warning = None
    if len(subject) > 50:
        subject_warning = f"subject exceeds 50 characters ({len(subject)} chars)"

    # Remove ending period from subject if present
    if subject.endswith("."):
        subject = subject[:-1]

    # Capitalize first letter of subject
    if subject and subject[0].islower():
        subject = subject[0].upper() + subject[1:]

    # Parse body
    body_lines = lines[1:]
    # Drop empty lines immediately following subject
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    if not body_lines:
        new_text = subject + "\n"
        return ReflowResult(new_text, subject_warning, new_text != raw_text)

    # Process body paragraphs
    formatted_body_blocks: list[str] = []
    current_para_lines: list[str] = []
    in_code_block = False

    def flush_para():
        if not current_para_lines:
            return
        para_text = " ".join(current_para_lines)
        wrapped = textwrap.fill(
            para_text,
            width=72,
            break_long_words=False,
            break_on_hyphens=False,
        )
        formatted_body_blocks.append(wrapped)
        current_para_lines.clear()

    i = 0
    while i < len(body_lines):
        line = body_lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_para()
            in_code_block = not in_code_block
            formatted_body_blocks.append(line)
            i += 1
            continue

        if in_code_block:
            formatted_body_blocks.append(line)
            i += 1
            continue

        if not stripped:
            flush_para()
            i += 1
            continue

        if is_list_item(line) or is_block_boundary(line):
            flush_para()
            # If list item is longer than 72, wrap with hanging indent
            indent_match = re.match(r"^(\s*[*+-]|\s*\d+\.)\s*", line)
            if indent_match and len(line) > 72:
                prefix = indent_match.group(0)
                subsequent_indent = " " * len(prefix)
                wrapped_list = textwrap.fill(
                    line,
                    width=72,
                    initial_indent="",
                    subsequent_indent=subsequent_indent,
                    break_long_words=False,
                    break_on_hyphens=False,
                )
                formatted_body_blocks.append(wrapped_list)
            else:
                formatted_body_blocks.append(line)
            i += 1
            continue

        # Standard prose line
        current_para_lines.append(stripped)
        i += 1

    flush_para()

    final_body = "\n\n".join(formatted_body_blocks)
    new_text = f"{subject}\n\n{final_body}\n"
    changed = (new_text != raw_text)
    return ReflowResult(new_text, subject_warning, changed)


if __name__ == "__main__":
    import sys
    input_text = sys.stdin.read()
    res = reflow_commit_message(input_text)
    if res.subject_warning:
        sys.stderr.write(f"Warning: {res.subject_warning}\n")
    sys.stdout.write(res.text)
