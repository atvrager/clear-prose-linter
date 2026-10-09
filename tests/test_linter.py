"""test_linter.py - Unit tests for prose_lint and reflow_commit."""

import tempfile
from pathlib import Path

from prose_lint import (
    Severity,
    apply_fixes,
    lint_commit_message,
    lint_ste,
    lint_strunk_and_white,
)
from scripts.reflow_commit import reflow_commit_message


def test_commit_valid():
    msg = "Add user authentication\n\nThis commit adds authentication.\nIt uses token verification.\n"
    findings = lint_commit_message(msg)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert len(errors) == 0


def test_commit_subject_length():
    subject_51 = "A" * 51
    msg = f"{subject_51}\n\nBody here.\n"
    findings = lint_commit_message(msg)
    err = [f for f in findings if f.rule_id == "COMMIT001"]
    assert len(err) == 1
    assert "exceeds 50 characters" in err[0].message


def test_commit_subject_case():
    msg = "lowercase subject\n\nBody here.\n"
    findings = lint_commit_message(msg)
    err = [f for f in findings if f.rule_id == "COMMIT002"]
    assert len(err) == 1


def test_commit_subject_period():
    msg = "Add user authentication.\n\nBody here.\n"
    findings = lint_commit_message(msg)
    err = [f for f in findings if f.rule_id == "COMMIT003"]
    assert len(err) == 1


def test_commit_missing_blank_line():
    msg = "Add user authentication\nMissing blank line body.\n"
    findings = lint_commit_message(msg)
    err = [f for f in findings if f.rule_id == "COMMIT004"]
    assert len(err) == 1


def test_commit_body_line_length():
    long_line = "B" * 73
    msg = f"Add user authentication\n\n{long_line}\n"
    findings = lint_commit_message(msg)
    err = [f for f in findings if f.rule_id == "COMMIT005"]
    assert len(err) == 1


def test_reflow_commit():
    raw = (
        "add new feature\n"
        "Here is a very long paragraph that goes way past seventy two characters "
        "and needs to be wrapped properly without breaking words.\n"
        "* Item 1 with long description that needs proper hanging indentation.\n"
    )
    res = reflow_commit_message(raw)
    assert res.changed is True
    lines = res.text.splitlines()
    assert lines[0] == "Add new feature"
    assert lines[1] == ""
    for line in lines[2:]:
        assert len(line) <= 72


def test_strunk_and_white_lint():
    sample = (
        "We should utilize this feature.\n"
        "There is the question as to whether it works.\n"
        "We saw red, green and blue.\n"
    )
    findings = lint_strunk_and_white("test.md", sample)
    rule_ids = [f.rule_id for f in findings]
    assert "SW017" in rule_ids
    assert "SW002" in rule_ids


def test_ste_lint():
    sample = (
        "We don't support this; write two sentences.\n"
        "Use options, e.g. verbose mode.\n"
    )
    findings = lint_ste("test.md", sample)
    rule_ids = [f.rule_id for f in findings]
    assert "STE002" in rule_ids
    assert "STE003" in rule_ids
    assert "STE004" in rule_ids


def test_apply_fixes():
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md") as tmp:
        tmp.write("We should utilize this tool.\n")
        tmp_path = Path(tmp.name)

    try:
        findings = lint_strunk_and_white(str(tmp_path), tmp_path.read_text())
        fixed = apply_fixes(tmp_path, findings)
        assert fixed > 0
        content = tmp_path.read_text()
        assert "use" in content
        assert "utilize" not in content
    finally:
        tmp_path.unlink()
