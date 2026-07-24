# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Expanded transliteration test suite for decomposed Unicode nukta sequences (ড়/ঢ়/য়)
- Benchmark comparison against `indic_transliteration` (ISO 15919) on formal-register text
- JOSS submission paper

## [0.1.0] — 2026-07-08

### Added
- `detector.py` — script detection across Bangla, Latin, Arabic, Devanagari, Chakma, and Myanmar Unicode ranges via `detect_script()` and `is_bangla()`
- `normalizer.py` — Bangla Unicode normalization: NFC normalization, ZWJ/ZWNJ cleanup, Bangla↔ASCII digit conversion, punctuation normalization, invisible-character removal
- `tokenizer.py` — `word_tokenize()`, `sentence_tokenize()` (with Bangla danda/double-danda support), and `char_tokenize()`
- `romanizer.py` — deterministic Bangla→Roman transliteration (`romanize()`, `romanize_word()`, `romanize_tokens()`) using an NLC-style practical scheme, with:
  - Word-boundary inherent-vowel suppression (fixes naive romanizers producing e.g. `bangladesho` instead of `bangladesh`)
  - Explicit handling of decomposed nukta sequences (ড়/ঢ়/য় as base consonant + U+09BC)
- Full test suite (55 tests, `tests/test_all.py`) covering all four modules
- Zero runtime dependencies — pure Python standard library only
- MIT license, PyPI packaging via `pyproject.toml`

### Fixed
- Romanizer previously appended an inherent vowel to word-final consonants unconditionally; now suppressed at word boundaries (space, punctuation, end of string)
- Romanizer previously mishandled decomposed nukta sequences (consonant + U+09BC combining mark), producing incorrect output for words like বিশ্ববিদ্যালয়

[Unreleased]: https://github.com/itsrashedhasan/bangla-nlpkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/itsrashedhasan/bangla-nlpkit/releases/tag/v0.1.0
