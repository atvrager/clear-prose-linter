"""test_vale_rules.py - Smoke test for generated Vale YAML rules."""

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
VALE_DIRS = [ROOT / "styles" / "StrunkWhite", ROOT / "styles" / "STE"]


def test_vale_rules_syntax():
    yaml_files = []
    for d in VALE_DIRS:
        assert d.is_dir(), f"Missing directory {d}"
        yaml_files.extend(list(d.glob("*.yml")))

    assert len(yaml_files) >= 5, f"Expected at least 5 Vale rules, found {len(yaml_files)}"

    for yf in yaml_files:
        content = yf.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        assert isinstance(data, dict), f"{yf} did not parse as a dictionary"
        assert "extends" in data, f"{yf} missing 'extends'"
        assert "message" in data, f"{yf} missing 'message'"
        assert "level" in data, f"{yf} missing 'level'"
        assert "tokens" in data or "swap" in data, f"{yf} missing 'tokens' or 'swap'"
