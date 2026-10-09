#!/usr/bin/env python3
"""prose_lint.py - Unified prose linter fusing Strunk & White and ASD-STE100.

Usage:
  prose_lint.py [files...]            # lints files (defaults to git-tracked prose)
  prose_lint.py --commit < msgfile    # lints a git commit message
  prose_lint.py --fix-commit < msgfile # reflows a commit message to 50/72 standard
  prose_lint.py --fix [files...]      # automatically fixes unambiguous violations
  prose_lint.py --diff                # lints staged git changes
  prose_lint.py init <dir>            # initializes a new Git+Bazel project
  prose_lint.py install <dir>         # installs linter and hooks into existing project
"""

from __future__ import annotations

import argparse
import enum
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

SELF_DIR = Path(__file__).resolve().parent
if (SELF_DIR / "sw_rules.json").exists():
    SCRIPTS_DIR = SELF_DIR
    TEMPLATES_DIR = SELF_DIR.parent / "templates"
else:
    SCRIPTS_DIR = SELF_DIR / "skills" / "clear-prose" / "scripts"
    TEMPLATES_DIR = SELF_DIR / "templates"

SW_RULES_FILE = SCRIPTS_DIR / "sw_rules.json"
STE_RULES_FILE = SCRIPTS_DIR / "ste_rules.json"

PROSE_EXTS = frozenset({".md", ".txt", ".rst", ".adoc"})
SKIP_DIRS = frozenset({
    ".git",
    ".lake",
    "bazel-bin",
    "bazel-out",
    "bazel-testlogs",
    "node_modules",
    "third_party",
    "fixtures",
    "references",
})


class Severity(enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"


@dataclass
class Finding:
    file: str
    line: int
    col: int
    severity: Severity
    rule_id: str
    message: str
    context: str
    replacement: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


def load_rules() -> tuple[dict, dict]:
    """Loads Strunk & White and STE rules from JSON."""
    sw_rules = {}
    ste_rules = {}
    if SW_RULES_FILE.exists():
        with open(SW_RULES_FILE, "r", encoding="utf-8") as f:
            sw_rules = json.load(f)
    if STE_RULES_FILE.exists():
        with open(STE_RULES_FILE, "r", encoding="utf-8") as f:
            ste_rules = json.load(f)
    return sw_rules, ste_rules


SW_RULES, STE_RULES = load_rules()


def determine_mode(file_path: Path, content: str, default_mode: str) -> str:
    """Detects mode contextually from pragma, path, or CLI default."""
    if default_mode != "auto":
        return default_mode

    # Check top lines for pragma
    first_lines = "\n".join(content.splitlines()[:5])
    if re.search(r"<!--\s*style:\s*(ste|asd-ste100)\s*-->", first_lines, re.I):
        return "ste"
    if re.search(r"<!--\s*style:\s*(sw|strunk-white)\s*-->", first_lines, re.I):
        return "sw"

    path_str = str(file_path).lower()
    if any(k in path_str for k in ("/tasks/", "/specs/", "/verification/", "/rtl/")):
        return "ste"
    if any(k in path_str for k in ("/docs/", "/proposals/", "readme.md")):
        return "sw"

    return "sw"


# Passive voice pattern: auxiliary be verb + past participle
PASSIVE_PATTERN = re.compile(
    r"\b(am|is|are|was|were|be|been|being)\s+([a-z]+ed|written|made|done|seen|built|set|put|given|taken|shown)\b",
    re.I,
)

# Serial comma pattern: A, B and/or C without comma before conjunction
SERIAL_COMMA_PATTERN = re.compile(
    r"\b([A-Za-z0-9_-]+),\s+([A-Za-z0-9_-]+)\s+(and|or)\s+([A-Za-z0-9_-]+)\b",
    re.I,
)


def lint_strunk_and_white(file_name: str, content: str) -> list[Finding]:
    """Lints text using Strunk & White rules."""
    findings: list[Finding] = []
    lines = content.splitlines()

    # Needless words & Chapter IV misused words
    replacements = SW_RULES.get("needless_words", [])
    qualifiers = set(SW_RULES.get("qualifiers", ["very", "rather", "little", "pretty"]))

    for lineno, line in enumerate(lines, start=1):
        if line.strip().startswith("```") or line.strip().startswith("<!--"):
            continue

        # Check needless words
        for item in replacements:
            pat = item["pattern"]
            rep = item["replacement"]
            regex = r"\b" + re.escape(pat) + r"\b" if " " not in pat else r"\b" + r"\s+".join(re.escape(w) for w in pat.split()) + r"\b"
            for m in re.finditer(regex, line, re.I):
                findings.append(Finding(
                    file=file_name,
                    line=lineno,
                    col=m.start() + 1,
                    severity=Severity.WARNING,
                    rule_id="SW017",
                    message=f"Omit needless words: use '{rep}' instead of '{m.group(0)}'",
                    context=line.strip(),
                    replacement=rep,
                ))

        # Check Oxford comma (Rule 2)
        for m in SERIAL_COMMA_PATTERN.finditer(line):
            # Check if there is already a comma
            sub = line[m.start():m.end()]
            if "," in sub.split()[-2]:
                continue
            findings.append(Finding(
                file=file_name,
                line=lineno,
                col=m.start() + 1,
                severity=Severity.SUGGESTION,
                rule_id="SW002",
                message=f"In a series of three or more terms, use an Oxford comma before '{m.group(3)}'",
                context=sub,
            ))

        # Check Passive Voice (Principle 14)
        for m in PASSIVE_PATTERN.finditer(line):
            findings.append(Finding(
                file=file_name,
                line=lineno,
                col=m.start() + 1,
                severity=Severity.SUGGESTION,
                rule_id="SW014",
                message=f"Prefer active voice over '{m.group(0)}'",
                context=line.strip(),
            ))

        # Check Overused Qualifiers (Chapter V Reminder 8)
        for q in qualifiers:
            regex = r"\b" + re.escape(q) + r"\b"
            for m in re.finditer(regex, line, re.I):
                findings.append(Finding(
                    file=file_name,
                    line=lineno,
                    col=m.start() + 1,
                    severity=Severity.SUGGESTION,
                    rule_id="SW023",
                    message=f"Avoid qualifier '{m.group(0)}'",
                    context=line.strip(),
                ))

    return findings


def lint_ste(file_name: str, content: str) -> list[Finding]:
    """Lints text using ASD-STE100 rules."""
    findings: list[Finding] = []
    lines = content.splitlines()

    contractions = STE_RULES.get("contractions", [])
    latin = STE_RULES.get("latin_abbreviations", {})
    wordy = STE_RULES.get("wordy_phrases", {})

    in_code_block = False

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not stripped:
            continue

        # Semicolons forbidden (STE002)
        if ";" in line:
            findings.append(Finding(
                file=file_name,
                line=lineno,
                col=line.index(";") + 1,
                severity=Severity.ERROR,
                rule_id="STE002",
                message="Do not use semicolons; write two sentences",
                context=stripped,
            ))

        # Contractions (STE003)
        for c in contractions:
            for m in re.finditer(r"\b" + re.escape(c) + r"\b", line, re.I):
                findings.append(Finding(
                    file=file_name,
                    line=lineno,
                    col=m.start() + 1,
                    severity=Severity.ERROR,
                    rule_id="STE003",
                    message=f"Do not use contraction '{m.group(0)}'",
                    context=stripped,
                ))

        # Latin abbreviations (STE004)
        for lat, rep in latin.items():
            for m in re.finditer(r"(?:\b|\s)" + re.escape(lat), line, re.I):
                findings.append(Finding(
                    file=file_name,
                    line=lineno,
                    col=m.start() + 1,
                    severity=Severity.ERROR,
                    rule_id="STE004",
                    message=f"Spell out Latin abbreviation '{lat}' as '{rep}'",
                    context=stripped,
                    replacement=rep,
                ))

        # Wordy phrases (STE005)
        for w, rep in wordy.items():
            for m in re.finditer(r"\b" + re.escape(w) + r"\b", line, re.I):
                findings.append(Finding(
                    file=file_name,
                    line=lineno,
                    col=m.start() + 1,
                    severity=Severity.WARNING,
                    rule_id="STE005",
                    message=f"Use short form '{rep}' instead of '{w}'",
                    context=stripped,
                    replacement=rep,
                ))

        # Sentence length check (STE001: max 20 procedural, 25 descriptive)
        # Approximate sentence split by period + space
        sentences = re.split(r"(?<=[.!?])\s+", stripped)
        for s in sentences:
            words = [w for w in s.split() if any(c.isalnum() for c in w)]
            if len(words) > 25:
                findings.append(Finding(
                    file=file_name,
                    line=lineno,
                    col=1,
                    severity=Severity.ERROR,
                    rule_id="STE001",
                    message=f"Sentence has {len(words)} words (limit is 25 descriptive, 20 procedural)",
                    context=s[:80],
                ))
            elif len(words) > 20:
                findings.append(Finding(
                    file=file_name,
                    line=lineno,
                    col=1,
                    severity=Severity.WARNING,
                    rule_id="STE001",
                    message=f"Sentence has {len(words)} words (procedural limit is 20 words)",
                    context=s[:80],
                ))

    return findings


def lint_commit_message(text: str, name: str = "<commit>") -> list[Finding]:
    """Enforces strict 50-char subject and 72-char body rules on commit messages."""
    findings: list[Finding] = []
    lines = text.splitlines()

    # Find subject line
    subject_idx = next((i for i, line in enumerate(lines) if line.strip()), None)
    if subject_idx is None:
        return [Finding(name, 1, 1, Severity.ERROR, "COMMIT000", "Commit message is empty", "")]

    subject = lines[subject_idx].rstrip()
    sub_line_no = subject_idx + 1

    # COMMIT001: Subject max 50 chars
    if len(subject) > 50:
        findings.append(Finding(
            name,
            sub_line_no,
            51,
            Severity.ERROR,
            "COMMIT001",
            f"Subject exceeds 50 characters ({len(subject)} characters)",
            subject,
        ))

    # COMMIT002: Capitalization
    if subject and subject[0].islower():
        findings.append(Finding(
            name,
            sub_line_no,
            1,
            Severity.ERROR,
            "COMMIT002",
            "Capitalize the subject line",
            subject,
        ))

    # COMMIT003: No period at end of subject
    if subject.endswith("."):
        findings.append(Finding(
            name,
            sub_line_no,
            len(subject),
            Severity.ERROR,
            "COMMIT003",
            "Do not end the subject line with a period",
            subject,
        ))

    # COMMIT006: No WIP / fixup / squash
    if re.match(r"^(wip|fixup!|squash!)\b", subject, re.I):
        findings.append(Finding(
            name,
            sub_line_no,
            1,
            Severity.ERROR,
            "COMMIT006",
            "Do not commit WIP, fixup, or squash tags",
            subject,
        ))

    # Remaining lines check
    body_lines = lines[subject_idx + 1:]
    if body_lines:
        # COMMIT004: Blank line after subject
        if body_lines[0].strip():
            findings.append(Finding(
                name,
                sub_line_no + 1,
                1,
                Severity.ERROR,
                "COMMIT004",
                "Leave a blank line between the subject and the body",
                body_lines[0],
            ))

        for idx, line in enumerate(body_lines, start=sub_line_no + 1):
            # COMMIT007: Trailing whitespace
            if line.endswith(" ") or line.endswith("\t"):
                findings.append(Finding(
                    name,
                    idx,
                    len(line),
                    Severity.WARNING,
                    "COMMIT007",
                    "Line contains trailing whitespace",
                    line,
                ))

            # COMMIT005: Body line wrap 72 chars
            if len(line) > 72 and not line.strip().startswith("```") and not line.strip().startswith("http"):
                findings.append(Finding(
                    name,
                    idx,
                    73,
                    Severity.ERROR,
                    "COMMIT005",
                    f"Body line exceeds 72 characters ({len(line)} characters)",
                    line[:80],
                ))

        # Check body text against STE rules
        body_text = "\n".join(body_lines)
        ste_findings = lint_ste(name, body_text)
        for f in ste_findings:
            f.line += sub_line_no
            findings.append(f)

    return findings


def apply_fixes(file_path: Path, findings: list[Finding]) -> int:
    """Applies safe replacements to a file."""
    fixable = [f for f in findings if f.replacement is not None]
    if not fixable:
        return 0

    content = file_path.read_text(encoding="utf-8")
    original = content
    # Sort findings reverse by position so earlier replacements don't shift later ones
    for f in sorted(fixable, key=lambda x: (x.line, x.col), reverse=True):
        lines = content.splitlines(keepends=True)
        if f.line - 1 < len(lines):
            line = lines[f.line - 1]
            # Replace first instance of matched pattern near col
            if f.rule_id == "SW017" or f.rule_id == "STE005" or f.rule_id == "STE004":
                # Find matching term
                for item in SW_RULES.get("needless_words", []) + [
                    {"pattern": k, "replacement": v} for k, v in STE_RULES.get("latin_abbreviations", {}).items()
                ]:
                    if item.get("replacement") == f.replacement:
                        pat = item["pattern"]
                        line = re.sub(r"\b" + re.escape(pat) + r"\b", f.replacement, line, count=1, flags=re.I)
                        lines[f.line - 1] = line
                        break
            content = "".join(lines)

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        return len(fixable)
    return 0


def get_git_tracked_prose(repo_root: Path = Path(".")) -> list[Path]:
    """Finds all git-tracked prose files."""
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        files = []
        for line in res.stdout.splitlines():
            p = repo_root / line
            if p.suffix.lower() in PROSE_EXTS and p.is_file():
                parts = set(p.parts)
                if not parts.intersection(SKIP_DIRS):
                    files.append(p)
        return files
    except Exception:
        return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified prose linter fusing Strunk & White and ASD-STE100")
    parser.add_argument("paths", nargs="*", help="Files or directories to lint")
    parser.add_argument("--mode", choices=["auto", "sw", "ste"], default="auto", help="Prose style mode")
    parser.add_argument("--commit", action="store_true", help="Lint commit message from stdin or file")
    parser.add_argument("--fix-commit", action="store_true", help="Reflow commit message to 50/72 standard")
    parser.add_argument("--fix", action="store_true", help="Automatically apply safe word replacements")
    parser.add_argument("--diff", action="store_true", help="Lint only staged git changes")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Output format")

    # Subcommands
    if len(sys.argv) > 1 and sys.argv[1] in ("init", "install"):
        from scripts.project_installer import init_new_project, install_to_project
        cmd = sys.argv[1]
        target = sys.argv[2] if len(sys.argv) > 2 else "."
        fn = init_new_project if cmd == "init" else install_to_project
        res = fn(target)
        print(f"Project {cmd} completed:")
        for r in res:
            print(f"  - {r}")
        return 0

    args = parser.parse_args()

    # Commit reflow mode
    if args.fix_commit:
        from scripts.reflow_commit import reflow_commit_message
        raw = sys.stdin.read() if not args.paths else Path(args.paths[0]).read_text(encoding="utf-8")
        res = reflow_commit_message(raw)
        if res.subject_warning:
            sys.stderr.write(f"Warning: {res.subject_warning}\n")
        sys.stdout.write(res.text)
        return 0

    # Commit lint mode
    if args.commit:
        raw = sys.stdin.read() if not args.paths else Path(args.paths[0]).read_text(encoding="utf-8")
        name = args.paths[0] if args.paths else "<stdin>"
        findings = lint_commit_message(raw, name)
        errors = [f for f in findings if f.severity == Severity.ERROR]
        if args.format == "json":
            print(json.dumps([f.to_dict() for f in findings], indent=2))
        else:
            for f in findings:
                lvl = f.severity.value.upper()
                print(f"{f.file}:{f.line}:{f.col} [{lvl}] {f.rule_id}: {f.message}")
        return 1 if errors else 0

    # Prose file mode
    target_files: list[Path] = []
    if args.paths:
        for p_str in args.paths:
            p = Path(p_str)
            if p.is_file():
                target_files.append(p)
            elif p.is_dir():
                for root, dirs, files in os.walk(p):
                    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                    for f in files:
                        fp = Path(root) / f
                        if fp.suffix.lower() in PROSE_EXTS:
                            target_files.append(fp)
    else:
        # Default to git-tracked prose
        target_files = get_git_tracked_prose()

    if not target_files:
        if args.format == "text":
            print("No prose files found to lint.")
        return 0

    all_findings: list[Finding] = []

    for file_path in target_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        mode = determine_mode(file_path, content, args.mode)
        if mode == "ste":
            file_findings = lint_ste(str(file_path), content)
        else:
            file_findings = lint_strunk_and_white(str(file_path), content)

        if args.fix:
            applied = apply_fixes(file_path, file_findings)
            if applied > 0:
                print(f"Applied {applied} fixes to {file_path}")

        all_findings.extend(file_findings)

    # Output formatting
    errors = [f for f in all_findings if f.severity == Severity.ERROR]

    if args.format == "json":
        print(json.dumps([f.to_dict() for f in all_findings], indent=2))
    elif args.format == "markdown":
        print(f"## Prose Lint Report: {len(all_findings)} finding(s)\n")
        for f in all_findings:
            print(f"- **{f.file}:{f.line}** [{f.severity.value}] `{f.rule_id}`: {f.message}")
    else:
        for f in all_findings:
            lvl = f.severity.value.upper()
            print(f"{f.file}:{f.line}:{f.col} [{lvl}] {f.rule_id}: {f.message}")
        if all_findings:
            print(f"\nTotal findings: {len(all_findings)} ({len(errors)} error(s))")
        else:
            print("All prose files clean.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
