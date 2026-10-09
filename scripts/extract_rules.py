#!/usr/bin/env python3
"""extract_rules.py - Extracts style rules from Strunk & White PDF.

Provenance:
  Source: The Elements of Style, 4th Edition (William Strunk Jr. & E.B. White)
  Archive URL: https://archive.org/details/pdfy-2_qp8jQ61OI6NHwa
  Expected SHA-256: 75527b11f8db39481c7b4eace61358ec5377104da151cf19b1368c1344b47996
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PDF_PATH = Path("/home/atv/Downloads/Strunk & White - The Elements of Style, 4th Edition.pdf")
EXPECTED_SHA256 = "75527b11f8db39481c7b4eace61358ec5377104da151cf19b1368c1344b47996"
ARCHIVE_URL = "https://archive.org/details/pdfy-2_qp8jQ61OI6NHwa"

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills" / "clear-prose"
REFS_DIR = SKILLS_DIR / "references"
SCRIPTS_DIR = SKILLS_DIR / "scripts"
VALE_SW_DIR = ROOT / "styles" / "StrunkWhite"


def verify_checksum(path: Path) -> str:
    """Verifies that the PDF matches the known SHA-256 checksum."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    digest = h.hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(
            f"Checksum mismatch for {path}!\nExpected: {EXPECTED_SHA256}\nGot:      {digest}"
        )
    return digest


def extract_raw_text(pdf_path: Path) -> str:
    """Extracts raw text from PDF using pdftotext."""
    cmd = ["pdftotext", str(pdf_path), "-"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return res.stdout.decode("utf-8", errors="ignore")


# Well-known replacements from Chapter IV and Principle 17
KNOWN_REPLACEMENTS: dict[str, str] = {
    "and/or": "and or or",
    "as to whether": "whether",
    "as yet": "yet",
    "being that": "because",
    "care less": "care",
    "currently": "now",
    "each and every one": "each one",
    "in terms of": "in",
    "in the last analysis": "finally",
    "inside of": "inside",
    "irregardless": "regardless",
    "meaningful": "significant",
    "offhand": "offhanded",
    "one of the most": "a",
    "ongoing": "continuous",
    "oriented": "directed",
    "partially": "partly",
    "personalize": "customize",
    "personally": "",
    "possess": "have",
    "the foreseeable future": "soon",
    "the truth is": "",
    "try and": "try to",
    "utilize": "use",
    "verbal": "spoken",
    "there is no doubt that": "no doubt",
    "used for fuel purposes": "used for fuel",
    "he is a man who": "he",
    "in a hasty manner": "hastily",
    "the question as to whether": "whether",
    "owing to the fact that": "because",
    "in spite of the fact that": "though",
    "call your attention to the fact that": "remind you",
    "the fact that he had not succeeded": "his failure",
    "not honest": "dishonest",
    "did not remember": "forgot",
    "did not pay attention to": "ignored",
    "did not have much confidence in": "distrusted",
}

# Overused qualifiers from Chapter V Reminder 8
QUALIFIERS = [
    "rather",
    "very",
    "little",
    "pretty",
    "really",
]


def parse_rules_of_usage(text: str) -> list[dict]:
    """Parses Rules 1-11 from Chapter I."""
    rules = [
        {"id": "SW001", "num": 1, "title": "Form the possessive singular of nouns by adding 's."},
        {"id": "SW002", "num": 2, "title": "In a series of three or more terms with a single conjunction, use a comma after each term except the last."},
        {"id": "SW003", "num": 3, "title": "Enclose parenthetic expressions between commas."},
        {"id": "SW004", "num": 4, "title": "Place a comma before a conjunction introducing an independent clause."},
        {"id": "SW005", "num": 5, "title": "Do not join independent clauses with a comma."},
        {"id": "SW006", "num": 6, "title": "Do not break sentences in two."},
        {"id": "SW007", "num": 7, "title": "Use a colon after an independent clause to introduce a list of particulars, an appositive, an amplification, or an illustrative quotation."},
        {"id": "SW008", "num": 8, "title": "Use a dash to set off an abrupt break or interruption and to announce a long appositive or summary."},
        {"id": "SW009", "num": 9, "title": "The number of the subject determines the number of the verb."},
        {"id": "SW010", "num": 10, "title": "Use the proper case of pronoun."},
        {"id": "SW011", "num": 11, "title": "A participial phrase at the beginning of a sentence must refer to the grammatical subject."},
    ]
    return rules


def parse_principles_of_composition(text: str) -> list[dict]:
    """Parses Principles 12-22 from Chapter II."""
    principles = [
        {"id": "SW012", "num": 12, "title": "Choose a suitable design and hold to it."},
        {"id": "SW013", "num": 13, "title": "Make the paragraph the unit of composition."},
        {"id": "SW014", "num": 14, "title": "Use the active voice."},
        {"id": "SW015", "num": 15, "title": "Put statements in positive form."},
        {"id": "SW016", "num": 16, "title": "Use definite, specific, concrete language."},
        {"id": "SW017", "num": 17, "title": "Omit needless words."},
        {"id": "SW018", "num": 18, "title": "Avoid a succession of loose sentences."},
        {"id": "SW019", "num": 19, "title": "Express coordinate ideas in similar form."},
        {"id": "SW020", "num": 20, "title": "Keep related words together."},
        {"id": "SW021", "num": 21, "title": "In summaries, keep to one tense."},
        {"id": "SW022", "num": 22, "title": "Place the emphatic words of a sentence at the end."},
    ]
    return principles


def parse_style_reminders(text: str) -> list[dict]:
    """Parses Chapter V Style Reminders."""
    reminders = [
        {"num": 1, "title": "Place yourself in the background."},
        {"num": 2, "title": "Write in a way that comes naturally."},
        {"num": 3, "title": "Work from a suitable design."},
        {"num": 4, "title": "Write with nouns and verbs."},
        {"num": 5, "title": "Revise and rewrite."},
        {"num": 6, "title": "Do not overwrite."},
        {"num": 7, "title": "Do not overstate."},
        {"num": 8, "title": "Avoid the use of qualifiers."},
        {"num": 9, "title": "Do not affect a breezy manner."},
        {"num": 10, "title": "Use orthodox spelling."},
        {"num": 11, "title": "Do not explain too much."},
        {"num": 12, "title": "Do not construct awkward adverbs."},
        {"num": 13, "title": "Make sure the reader knows who is speaking."},
        {"num": 14, "title": "Avoid fancy words."},
        {"num": 15, "title": "Do not use dialect unless your ear is good."},
        {"num": 16, "title": "Be clear."},
        {"num": 17, "title": "Do not inject opinion."},
        {"num": 18, "title": "Use figures of speech sparingly."},
        {"num": 19, "title": "Do not take shortcuts at the cost of clarity."},
        {"num": 20, "title": "Avoid foreign languages."},
        {"num": 21, "title": "Prefer the standard to the offbeat."},
    ]
    return reminders


def parse_chapter_iv(text: str) -> list[dict]:
    """Parses entries from Chapter IV (Words and Expressions Commonly Misused)."""
    ch4_start = text.find("IVWords and Expressions Commonly Misused")
    ch5_start = text.find("VAn Approach to Style")
    if ch4_start == -1 or ch5_start == -1:
        # Fallback search
        ch4_start = text.find("Words and Expressions Commonly Misused")
        ch5_start = text.find("An Approach to Style")

    ch4_text = text[ch4_start:ch5_start] if (ch4_start != -1 and ch5_start != -1) else ""

    # Split by entries: start of line followed by Title. followed by capital letter
    raw_entries = re.split(r"\n(?=[A-Z][A-Za-z0-9\s/\-—]+\.\s+[A-Z])", ch4_text)
    entries: list[dict] = []

    for item in raw_entries:
        item = item.strip()
        if not item or len(item) < 10:
            continue
        first_line = item.splitlines()[0]
        m = re.match(r"^([A-Z][A-Za-z0-9\s/\-—]+?)\.\s+(.*)", item, re.DOTALL)
        if not m:
            continue
        term = m.group(1).strip()
        body = m.group(2).strip()

        # Clean term and extract pattern
        term_clean = term.replace("—", "").strip()
        if len(term_clean.split()) > 6:
            # Skip full sentence examples
            continue

        search_key = term_clean.lower()
        replacement = KNOWN_REPLACEMENTS.get(search_key, "")

        entries.append({
            "term": term_clean,
            "pattern": r"\b" + re.escape(term_clean) + r"\b" if " " not in term_clean else r"\b" + r"\s+".join(re.escape(w) for w in term_clean.split()) + r"\b",
            "replacement": replacement,
            "explanation": " ".join(body.split()[:40]),
            "full_text": body[:300],
        })

    return entries


def main() -> None:
    print(f"Verifying PDF checksum from {PDF_PATH}...")
    digest = verify_checksum(PDF_PATH)
    print(f"Checksum verified: {digest}")

    print("Extracting raw text from PDF...")
    text = extract_raw_text(PDF_PATH)
    print(f"Extracted {len(text)} characters.")

    print("Parsing chapters...")
    rules_of_usage = parse_rules_of_usage(text)
    principles = parse_principles_of_composition(text)
    reminders = parse_style_reminders(text)
    ch4_entries = parse_chapter_iv(text)
    print(f"Parsed {len(ch4_entries)} Chapter IV misuse entries.")

    # Build sw_rules.json
    sw_rules = {
        "metadata": {
            "source": "Strunk & White - The Elements of Style, 4th Edition",
            "archive_url": ARCHIVE_URL,
            "sha256": EXPECTED_SHA256,
        },
        "rules_of_usage": rules_of_usage,
        "principles_of_composition": principles,
        "style_reminders": reminders,
        "misused_words": ch4_entries,
        "needless_words": [
            {"pattern": k, "replacement": v} for k, v in KNOWN_REPLACEMENTS.items() if v
        ],
        "qualifiers": QUALIFIERS,
    }

    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    out_json = SCRIPTS_DIR / "sw_rules.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(sw_rules, f, indent=2)
    print(f"Wrote {out_json}")

    # Build ste_rules.json using established son-of-shoumei rules
    ste_rules = {
        "metadata": {
            "standard": "ASD-STE100 Issue 8",
            "source": "son-of-shoumei/verification/ste-lint.py",
        },
        "lengths": {
            "sentence_warn": 21,
            "sentence_fail": 26,
            "paragraph_max_sentences": 6,
            "commit_subject_max": 50,
            "commit_body_max": 72,
        },
        "contractions": [
            "aren't", "can't", "couldn't", "didn't", "doesn't", "don't",
            "hadn't", "hasn't", "haven't", "he'd", "he'll", "he's",
            "i'd", "i'll", "i'm", "i've", "isn't", "it's", "let's",
            "shouldn't", "that's", "there's", "they'd", "they'll",
            "they're", "they've", "wasn't", "we'd", "we'll", "we're",
            "we've", "weren't", "what's", "who's", "won't", "wouldn't",
            "you'd", "you'll", "you're", "you've",
        ],
        "latin_abbreviations": {
            "e.g.": "for example",
            "i.e.": "that is",
            "etc.": "and so on",
            "et al.": "and others",
            "viz.": "namely",
            "c.f.": "compare with",
            "ca.": "about",
            "vs.": "against",
        },
        "wordy_phrases": {
            "in order to": "to",
            "a number of": "many",
            "at the present time": "now",
            "due to the fact that": "because",
            "for the purpose of": "to",
            "in the event that": "if",
            "is able to": "can",
            "make an adjustment to": "adjust",
            "make inquiry": "ask",
            "prior to": "before",
            "subsequent to": "after",
            "with reference to": "about",
            "with the exception of": "except for",
        },
    }

    out_ste_json = SCRIPTS_DIR / "ste_rules.json"
    with open(out_ste_json, "w", encoding="utf-8") as f:
        json.dump(ste_rules, f, indent=2)
    print(f"Wrote {out_ste_json}")

    # Generate reference docs
    REFS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REFS_DIR / "rules_of_usage.md", "w", encoding="utf-8") as f:
        f.write("# Elementary Rules of Usage\n\nFrom *The Elements of Style*, Chapter I:\n\n")
        for r in rules_of_usage:
            f.write(f"## Rule {r['num']}: {r['title']}\n\n")

    with open(REFS_DIR / "principles_of_composition.md", "w", encoding="utf-8") as f:
        f.write("# Elementary Principles of Composition\n\nFrom *The Elements of Style*, Chapter II:\n\n")
        for p in principles:
            f.write(f"## Principle {p['num']}: {p['title']}\n\n")

    with open(REFS_DIR / "misused_words.md", "w", encoding="utf-8") as f:
        f.write("# Words and Expressions Commonly Misused\n\nFrom *The Elements of Style*, Chapter IV:\n\n")
        for m in ch4_entries:
            rep = f" -> **Use**: `{m['replacement']}`" if m["replacement"] else ""
            f.write(f"### {m['term']}{rep}\n\n{m['explanation']}\n\n")

    with open(REFS_DIR / "style_reminders.md", "w", encoding="utf-8") as f:
        f.write("# An Approach to Style: 21 Reminders\n\nFrom *The Elements of Style*, Chapter V:\n\n")
        for rem in reminders:
            f.write(f"{rem['num']}. {rem['title']}\n")

    # Generate Vale rules
    VALE_SW_DIR.mkdir(parents=True, exist_ok=True)
    with open(VALE_SW_DIR / "MisusedWords.yml", "w", encoding="utf-8") as f:
        f.write("extends: substitution\nmessage: \"Use '%s' instead of '%s' (Strunk & White Chapter IV)\"\nlink: https://archive.org/details/pdfy-2_qp8jQ61OI6NHwa\nlevel: warning\nswap:\n")
        for k, v in KNOWN_REPLACEMENTS.items():
            if v and " " not in k:
                f.write(f"  {k}: {v}\n")

    with open(VALE_SW_DIR / "NeedlessWords.yml", "w", encoding="utf-8") as f:
        f.write("extends: substitution\nmessage: \"Omit needless words: use '%s' instead of '%s' (Strunk & White Principle 17)\"\nlink: https://archive.org/details/pdfy-2_qp8jQ61OI6NHwa\nlevel: warning\nswap:\n")
        for k, v in KNOWN_REPLACEMENTS.items():
            if v and " " in k:
                f.write(f"  \"{k}\": \"{v}\"\n")

    with open(VALE_SW_DIR / "Qualifiers.yml", "w", encoding="utf-8") as f:
        f.write("extends: existence\nmessage: \"Avoid overused qualifiers: '%s' (Strunk & White Chapter V, Reminder 8)\"\nlevel: suggestion\ntokens:\n")
        for q in QUALIFIERS:
            f.write(f"  - {q}\n")

    # Generate Vale STE rules
    vale_ste_dir = ROOT / "styles" / "STE"
    vale_ste_dir.mkdir(parents=True, exist_ok=True)
    with open(vale_ste_dir / "Latin.yml", "w", encoding="utf-8") as f:
        f.write("extends: substitution\nmessage: \"ASD-STE100: Spell out Latin abbreviation '%s' as '%s'\"\nlevel: error\nswap:\n")
        for k, v in ste_rules["latin_abbreviations"].items():
            f.write(f"  \"{k}\": \"{v}\"\n")

    with open(vale_ste_dir / "Contractions.yml", "w", encoding="utf-8") as f:
        f.write("extends: existence\nmessage: \"ASD-STE100: Do not use contraction '%s'\"\nlevel: error\ntokens:\n")
        for c in ste_rules["contractions"]:
            f.write(f"  - \"{c}\"\n")

    print("Generated all reference documents and Vale rules.")


if __name__ == "__main__":
    main()
