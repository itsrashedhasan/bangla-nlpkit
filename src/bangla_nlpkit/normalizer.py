"""
normalizer.py — Bangla Unicode text normalization.

Handles common issues found in real-world Bangla text:
  - Incorrect Zero-Width Joiner / Non-Joiner placement
  - Inconsistent Unicode normalization forms
  - Mixed Bangla and ASCII digit usage
  - Non-standard punctuation variants
  - Extra whitespace and invisible characters
"""

from __future__ import annotations
import re
import unicodedata


# ---------------------------------------------------------------------------
# Unicode constants
# ---------------------------------------------------------------------------
_ZWJ  = "\u200D"   # Zero Width Joiner
_ZWNJ = "\u200C"   # Zero Width Non-Joiner

# Bangla Unicode block: U+0980–U+09FF
_BANGLA_CONSONANT_START = 0x0995   # ক
_BANGLA_CONSONANT_END   = 0x09B9   # হ
_HASANTA                = "\u09CD"  # ্  (virama — suppresses inherent vowel)

# Bangla numerals → ASCII digits
_BANGLA_DIGIT_MAP: dict[str, str] = {
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9",
}

# ASCII digits → Bangla numerals (reverse)
_ASCII_TO_BANGLA_MAP: dict[str, str] = {v: k for k, v in _BANGLA_DIGIT_MAP.items()}

# Non-standard punctuation normalizations
_PUNCTUATION_MAP: dict[str, str] = {
    "\u2018": "'",   # Left single quotation mark → ASCII apostrophe
    "\u2019": "'",   # Right single quotation mark
    "\u201C": '"',   # Left double quotation mark
    "\u201D": '"',   # Right double quotation mark
    "\u2013": "-",   # En dash
    "\u2014": "-",   # Em dash
    "\u2026": "...", # Ellipsis
}

# Invisible / control characters to strip (excludes \t, \n, \r)
_INVISIBLE_RE = re.compile(
    r"[\u00AD\u034F\u061C\u115F\u1160\u17B4\u17B5"
    r"\u180B-\u180D\u200B\u2028\u2029\u2060\uFEFF\uFFA0]"
)

# Multiple whitespace collapser
_MULTI_SPACE_RE = re.compile(r"[ \t]+")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_bangla_consonant(ch: str) -> bool:
    cp = ord(ch)
    return _BANGLA_CONSONANT_START <= cp <= _BANGLA_CONSONANT_END


def _clean_zwj(text: str) -> str:
    """
    Remove ZWJ/ZWNJ that appear in positions where they have no phonetic role.

    In correct Bangla typography:
    - ZWJ between a consonant + hasanta keeps the half-form (রেফ, যুক্তাক্ষর)
    - ZWNJ between consonant + hasanta forces the explicit hasanta to show

    We only strip them when they appear outside this pattern.
    """
    result: list[str] = []
    chars = list(text)
    n = len(chars)
    for i, ch in enumerate(chars):
        if ch in (_ZWJ, _ZWNJ):
            prev_ok = (i > 0 and _is_bangla_consonant(chars[i - 1]))
            next_ok = (i + 1 < n and chars[i + 1] == _HASANTA)
            if prev_ok and next_ok:
                result.append(ch)   # legitimate usage — keep
            # else: drop silently
        else:
            result.append(ch)
    return "".join(result)


def _normalize_digits(text: str, to_ascii: bool = True) -> str:
    table = _BANGLA_DIGIT_MAP if to_ascii else _ASCII_TO_BANGLA_MAP
    return text.translate(str.maketrans(table))


def _normalize_punctuation(text: str) -> str:
    return text.translate(str.maketrans(_PUNCTUATION_MAP))


def _normalize_whitespace(text: str) -> str:
    text = _INVISIBLE_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize(
    text: str,
    *,
    nfc: bool = True,
    remove_zwj: bool = True,
    normalize_digits: bool = False,
    to_ascii_digits: bool = True,
    normalize_punctuation: bool = True,
    strip: bool = True,
) -> str:
    """
    Normalize Bangla (and mixed-script) text.

    Parameters
    ----------
    text : str
        Raw input string.
    nfc : bool
        Apply Unicode NFC normalization (recommended, default True).
    remove_zwj : bool
        Remove incorrectly placed Zero Width Joiners/Non-Joiners (default True).
    normalize_digits : bool
        Convert between Bangla and ASCII digits (default False).
        When True, conversion direction is controlled by *to_ascii_digits*.
    to_ascii_digits : bool
        If *normalize_digits* is True and this is True, convert ০–৯ → 0–9.
        If False, convert 0–9 → ০–৯ (default True).
    normalize_punctuation : bool
        Replace curly quotes, em/en dashes, and ellipsis with ASCII equivalents
        (default True).
    strip : bool
        Strip leading/trailing whitespace from the final result (default True).

    Returns
    -------
    str
        Normalized text.

    Examples
    --------
    >>> normalize("  আমি  বাংলায়  কথা  বলি  ")
    'আমি বাংলায় কথা বলি'

    >>> normalize("আমার ০১৭৭৪ নম্বর", normalize_digits=True)
    'আমার 01774 নম্বর'

    >>> normalize("Hello "world"")
    'Hello "world"'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    if nfc:
        text = unicodedata.normalize("NFC", text)

    if remove_zwj:
        text = _clean_zwj(text)

    if normalize_digits:
        text = _normalize_digits(text, to_ascii=to_ascii_digits)

    if normalize_punctuation:
        text = _normalize_punctuation(text)

    text = _normalize_whitespace(text)

    if strip:
        text = text.strip()

    return text


def to_ascii_digits(text: str) -> str:
    """
    Convert Bangla numerals (০–৯) to ASCII digits (0–9).

    Examples
    --------
    >>> to_ascii_digits("আমার বয়স ২৩ বছর")
    'আমার বয়স 23 বছর'
    """
    return _normalize_digits(text, to_ascii=True)


def to_bangla_digits(text: str) -> str:
    """
    Convert ASCII digits (0–9) to Bangla numerals (০–৯).

    Examples
    --------
    >>> to_bangla_digits("আমার বয়স 23 বছর")
    'আমার বয়স ২৩ বছর'
    """
    return _normalize_digits(text, to_ascii=False)


def remove_invisible(text: str) -> str:
    """
    Remove invisible Unicode characters (zero-width spaces, BOM, soft hyphens, etc.)
    while preserving normal whitespace (space, tab, newline).

    Examples
    --------
    >>> remove_invisible("আমি\u200Bবাংলা")  # zero-width space between words
    'আমিবাংলা'
    """
    return _INVISIBLE_RE.sub("", text)