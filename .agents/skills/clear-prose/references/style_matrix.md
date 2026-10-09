# Style Selection Matrix: ASD-STE100 vs. Strunk & White

This matrix explains when to use Simplified Technical English (ASD-STE100) and when to use Strunk & White (*The Elements of Style*).

## Comparison Table

| Dimension | Simplified Technical English (ASD-STE100) | Strunk & White (*The Elements of Style*) |
| :--- | :--- | :--- |
| **Primary Goal** | Zero ambiguity, safety, strict machine/contract correctness | Clarity, vigor, conciseness, and natural flow |
| **Target Audience** | Machine parsers, international engineers, verification suites | System designers, library users, developers reading documentation |
| **Sentence Length** | 20 words max (procedural), 25 words max (descriptive) | Varied sentence lengths to avoid monotony and give emphasis |
| **Vocabulary** | Restricted to approved dictionary words with single meanings | Broad, natural vocabulary; prefers simple words to ornate ones |
| **Voice** | Active voice strictly required | Active voice strongly preferred; passive used only when necessary |
| **Contractions** | Strictly forbidden | Discouraged in formal writing; allowed where natural |
| **Serial Comma** | Comma after each list item | Oxford comma required before the conjunction |
| **Semicolons** | Forbidden (write two sentences) | Permitted to connect related independent clauses |

## Context Guidelines

### Choose ASD-STE100 Mode for:
- Hardware and RTL specifications (`specs/`, `rtl/`).
- Task verification contracts (`tasks/*.md`, `verification/`).
- Code comments explaining hardware registers, signals, and protocol states.
- Safety-critical system instructions.
- Git commit message bodies.

### Choose Strunk & White Mode for:
- Project overview and setup guides (`README.md`, `CONTRIBUTING.md`).
- Architecture and design proposal documents (`docs/`, `proposals/`, `rfcs/`).
- High-level API documentation.
- Technical blog posts and user-facing tutorials.

## How to Transition
1. Both styles enforce:
   - "Use the active voice."
   - "Omit needless words."
   - "Put statements in positive form."
2. When transitioning from STE to Strunk & White:
   - Remove the strict 20/25 word limit.
   - Use varied sentence lengths to create rhythm.
   - Expand your vocabulary, but continue to avoid fancy or pretentious words.
