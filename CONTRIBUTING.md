# Contributing to bangla-nlpkit

Thanks for your interest in improving bangla-nlpkit. This project is a small,
zero-dependency toolkit for Bangla text processing, and contributions of all
sizes are welcome — bug reports, documentation fixes, new test cases, and
feature proposals.

## Getting started

1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/bangla-nlpkit.git
   cd bangla-nlpkit
   ```

2. Install in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Run the test suite to confirm your environment is working:
   ```bash
   pytest tests/ -v
   ```

## Making changes

- **Create a branch** for your change: `git checkout -b fix/short-description`
- **Write tests** for any new behavior or bug fix. This project maintains full
  test coverage across all four modules (`detector`, `normalizer`, `tokenizer`,
  `romanizer`) — new code should follow the same standard.
- **Run the full test suite** before opening a pull request:
  ```bash
  pytest tests/ -v
  ```
- **Keep the zero-dependency policy.** This library intentionally has no
  runtime dependencies beyond the Python standard library. If your change
  requires a new dependency, please open an issue to discuss it first —
  it may be better suited as an optional extra or a separate package.

## Reporting bugs

When reporting a bug, especially in `romanizer.py` or `normalizer.py`, please
include:
- The exact input string (Bangla text, copy-pasted, not transliterated)
- The actual output vs. the expected output
- Whether the issue involves a specific Unicode edge case (e.g. decomposed
  nukta characters, conjuncts, word-final consonants)

Character-level Unicode bugs are the most common and most valuable category
of bug report for this project — please be as precise as possible about the
exact characters involved.

## Code style

- Follow the existing docstring format (NumPy-style, with `Parameters`,
  `Returns`, and `Examples` sections) for any new public function.
- Keep functions pure where possible — no hidden global state.
- Type hints are expected on all new public functions.

## Linting

```bash
ruff check src/
mypy src/
```

## Pull requests

- Reference any related issue in your PR description.
- Keep PRs focused on a single change where possible.
- Update `CHANGELOG.md` under an `[Unreleased]` heading describing your change.

## Questions

Open an issue at https://github.com/itsrashedhasan/bangla-nlpkit/issues for
questions, proposals, or discussion before starting larger changes.
