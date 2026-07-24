# bangla-nlpkit

A lightweight, zero-dependency Python toolkit for Bangla (Bengali) NLP — with support for Chakma, Myanmar (Marma), Devanagari, Arabic, and Latin scripts.

[![PyPI version](https://img.shields.io/pypi/v/bangla-nlpkit)](https://pypi.org/project/bangla-nlpkit/)
[![Python](https://img.shields.io/pypi/pyversions/bangla-nlpkit)](https://pypi.org/project/bangla-nlpkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

| Module | Functions | Description |
|---|---|---|
| `detector` | `detect_script`, `is_bangla` | Unicode-range script detection across 6 script families |
| `normalizer` | `normalize`, `to_ascii_digits`, `to_bangla_digits`, `remove_invisible` | Unicode cleanup, ZWJ/ZWNJ fix, digit conversion, whitespace normalization |
| `tokenizer` | `word_tokenize`, `sentence_tokenize`, `char_tokenize` | Bangla-aware word and sentence splitting with danda (।) support |
| `romanizer` | `romanize`, `romanize_word`, `romanize_tokens` | Bangla script → Roman transliteration (NLC scheme) |

**Zero external dependencies** — pure Python standard library only.

---

## Installation

```bash
pip install bangla-nlpkit
```

---

## Quick Start

```python
from bangla_nlpkit import detect_script, normalize, word_tokenize, romanize

# Script detection
result = detect_script("আমি বাংলায় কথা বলি")
print(result.dominant)          # bangla
print(result.scores)            # {'bangla': 1.0, 'latin': 0.0, ...}

# Mixed script
result = detect_script("আমি English মিশিয়ে বলি")
print(result.dominant)          # bangla
print(result.is_mixed())        # True

# Normalization
text = normalize("  আমি  বাংলায়  কথা  বলি  ")
print(text)                     # আমি বাংলায় কথা বলি

# Digit conversion
print(normalize("আমার বয়স ২৩", normalize_digits=True))   # আমার বয়স 23

# Tokenization
tokens = word_tokenize("আমি বাংলায় কথা বলি।")
print(tokens)   # ['আমি', 'বাংলায়', 'কথা', 'বলি']

sents = sentence_tokenize("আমি বাংলায় কথা বলি। তুমি কি বাংলায় কথা বলো?")
print(sents)    # ['আমি বাংলায় কথা বলি।', 'তুমি কি বাংলায় কথা বলো?']

# Romanization
print(romanize("বাংলাদেশ"))     # bangladesh
print(romanize("ঢাকা"))         # dhaka
print(romanize("মুক্তিযুদ্ধ")) # muktijuddho
```

---

## Supported Scripts

| Script | Languages | Unicode Range |
|---|---|---|
| Bangla | Bengali, Sylheti | U+0980–U+09FF |
| Latin | English, Garo | Basic Latin + Extended |
| Arabic | Arabic, Urdu | U+0600–U+06FF |
| Devanagari | Hindi, Sanskrit | U+0900–U+097F |
| Chakma | Chakma | U+11100–U+1114F |
| Myanmar | Marma (Burmese) | U+1000–U+109F |

> **Note:** Garo language uses Latin script and will be detected as `latin`. For language-level disambiguation between Garo and English, a language classifier model is required.

---

## API Reference

### `detect_script(text) → DetectionResult`

```python
result = detect_script("আমি বাংলায় কথা বলি")
result.dominant          # 'bangla'
result.scores            # {'bangla': 1.0, 'latin': 0.0, ...}
result.char_counts       # {'bangla': 18, 'latin': 0, ...}
result.total_classified  # 18
result.is_mixed()        # False
```

### `normalize(text, *, nfc, remove_zwj, normalize_digits, to_ascii_digits, normalize_punctuation, strip) → str`

```python
normalize("  আমি  বাংলায়  ")              # 'আমি বাংলায়'
normalize("আমার ২৩", normalize_digits=True) # 'আমার 23'
normalize("\u201Chello\u201D")              # '"hello"'
```

### `word_tokenize(text, *, keep_punctuation) → list[str]`

```python
word_tokenize("আমি বাংলায় কথা বলি।")                    # ['আমি', 'বাংলায়', 'কথা', 'বলি']
word_tokenize("আমি বলি।", keep_punctuation=True)         # ['আমি', 'বলি', '।']
```

### `sentence_tokenize(text) → list[str]`

```python
sentence_tokenize("বাক্য এক। বাক্য দুই।")
# ['বাক্য এক।', 'বাক্য দুই।']
```

### `romanize(text, *, passthrough_non_bangla) → str`

```python
romanize("বাংলাদেশ")                           # 'bangladesh'
romanize("আমি English মিশিয়ে বলি")            # 'ami English mishiye boli'
romanize("আমি English বলি", passthrough_non_bangla=False)  # 'ami  boli'
```

---

## Running Tests

```bash
pip install bangla-nlpkit[dev]
pytest tests/ -v
```

---

## Background

This library was developed alongside research on low-resource Bangladeshi languages (Bengali, Chakma, Garo, Marma) published at ITAI 2026 (Springer LNNS, Lasell University, USA). It addresses practical preprocessing gaps encountered when working with mixed-script parallel corpora.

---

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Rashedul Hasan Shohan**  
BSc CSE, Daffodil International University, Bangladesh  
[GitHub](https://github.com/itsrashedhasan) · [Google Scholar](https://scholar.google.com/citations?user=ET8FzOIAAAAJ) · [ORCID](https://orcid.org/0009-0004-9069-484X)