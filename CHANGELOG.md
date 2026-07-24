# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — Unreleased

### Fixed
- README's `romanize("মুক্তিযুদ্ধ")` example claimed output `muktijuddho`; actual
  (correct) output is `muktijuddh`. The example was written before the
  word-final inherent-vowel suppression fix and was never updated afterward.
- README's `romanize(..., passthrough_non_bangla=False)` example claimed output
  `'ami  boli'` (with surrounding spaces preserved); actual output is
  `'amiboli'`, since whitespace is itself a non-Bangla character and is
  dropped along with everything else when `passthrough_non_bangla=False`.

### Added
- Permanent regression test suite for decomposed-nukta handling
  (`TestRomanizeDecomposedNukta` in `tests/test_all.py`), derived from
  `benchmarks/benchmark_nukta.py`. Locks in the verified 40/40 correctness
  result as a CI-enforced gate rather than leaving it only in a benchmark
  script that isn't run automatically.
- `benchmarks/benchmark_nukta.py` — systematic 40-word test comparing
  bangla-nlpkit against `indic_transliteration` (ISO 15919) on decomposed
  vs. precomposed Unicode nukta sequences (ড়/ঢ়/য়). Result: bangla-nlpkit
  40/40 consistent, 0/40 leaked characters; indic_transliteration 0/40
  consistent, 40/40 leaked characters.
- `benchmarks/benchmark_latency.py` — controlled latency benchmark (10
  trials x 20,000 calls, median + mean reported, environment disclosed).
  Independently reproduced on Linux (4.86x) and Windows (4.16x), both
  showing bangla-nlpkit faster with <5% relative variance.
- `LICENSE`, `.gitignore`, `CONTRIBUTING.md`, `.github/workflows/tests.yml` (CI)

## [0.1.0] — 2026-07-08

### Added
- `detector.py` — script detection across Bangla, Latin, Arabic, Devanagari, Chakma, and Myanmar Unicode ranges via `detect_script()` and `is_bangla()`
- `normalizer.py` — Bangla Unicode normalization: NFC normalization, ZWJ/ZWNJ cleanup, Bangla<->ASCII digit conversion, punctuation normalization, invisible-character removal
- `tokenizer.py` — `word_tokenize()`, `sentence_tokenize()` (with Bangla danda/double-danda support), and `char_tokenize()`
- `romanizer.py` — deterministic Bangla->Roman transliteration (`romanize()`, `romanize_word()`, `romanize_tokens()`) using an NLC-style practical scheme, with:
  - Word-boundary inherent-vowel suppression (fixes naive romanizers producing e.g. `bangladesho` instead of `bangladesh`)
  - Explicit handling of decomposed nukta sequences (ড়/ঢ়/য় as base consonant + U+09BC)
- Full test suite (55 tests, `tests/test_all.py`) covering all four modules
- Zero runtime dependencies — pure Python standard library only
- MIT license, PyPI packaging via `pyproject.toml`

### Fixed
- Romanizer previously appended an inherent vowel to word-final consonants unconditionally; now suppressed at word boundaries (space, punctuation, end of string)
- Romanizer previously mishandled decomposed nukta sequences (consonant + U+09BC combining mark), producing incorrect output for words like বিশ্ববিদ্যালয়

[Unreleased]: https://github.com/itsrashedhasan/bangla-nlpkit/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/itsrashedhasan/bangla-nlpkit/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/itsrashedhasan/bangla-nlpkit/releases/tag/v0.1.0