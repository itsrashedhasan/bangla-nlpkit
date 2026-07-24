"""
romanizer.py — Bangla script to Roman (Latin) transliteration.

Uses a phoneme-accurate character mapping based on the National Library
at Calcutta (NLC) romanization scheme, adapted for practical readability.

Key rules implemented:
  - Consonants carry an inherent 'o' vowel unless:
      (a) followed by hasanta (্) — conjunct consonant, no vowel
      (b) followed by a vowel diacritic (matra) — explicit vowel replaces it
      (c) at word boundary (space / end of string / punctuation) — vowel dropped
  - Hasanta (্) between consonants suppresses the inherent vowel
  - Independent vowels are transliterated directly
  - Bangla numerals (০–৯) → ASCII digits
  - Non-Bangla characters are passed through unchanged
  - Decomposed forms of ড়/ঢ়/য় (base + nukta U+09BC) handled alongside
    their NFC precomposed forms
"""

from __future__ import annotations
import unicodedata


# ---------------------------------------------------------------------------
# Transliteration tables
# ---------------------------------------------------------------------------

# Independent vowels (used at the start of a syllable or after another vowel)
_VOWELS: dict[str, str] = {
    "অ": "o",   "আ": "a",   "ই": "i",   "ঈ": "i",
    "উ": "u",   "ঊ": "u",   "ঋ": "ri",  "এ": "e",
    "ঐ": "oi",  "ও": "o",   "ঔ": "ou",
}

# Vowel diacritics (matras — attached to consonants)
_MATRAS: dict[str, str] = {
    "া": "a",   "ি": "i",   "ী": "i",   "ু": "u",
    "ূ": "u",   "ৃ": "ri",  "ে": "e",   "ৈ": "oi",
    "ো": "o",   "ৌ": "ou",
}

# Nukta (U+09BC) — combines with the preceding consonant
_NUKTA = "\u09BC"

# Consonants (single Unicode char — precomposed forms preferred via NFC)
_CONSONANTS: dict[str, str] = {
    # Velar
    "ক": "k",   "খ": "kh",  "গ": "g",   "ঘ": "gh",  "ঙ": "ng",
    # Palatal
    "চ": "ch",  "ছ": "chh", "জ": "j",   "ঝ": "jh",  "ঞ": "ny",
    # Retroflex
    "ট": "t",   "ঠ": "th",  "ড": "d",   "ঢ": "dh",  "ণ": "n",
    # Dental
    "ত": "t",   "থ": "th",  "দ": "d",   "ধ": "dh",  "ন": "n",
    # Labial
    "প": "p",   "ফ": "ph",  "ব": "b",   "ভ": "bh",  "ম": "m",
    # Approximants & fricatives
    "য": "j",   "র": "r",   "ল": "l",
    "শ": "sh",  "ষ": "sh",  "স": "s",   "হ": "h",
    # Special consonants — precomposed (NFC) forms
    "\u09DC": "r",   # ড় precomposed
    "\u09DD": "rh",  # ঢ় precomposed
    "\u09DF": "y",   # য় precomposed
    "ৎ": "t",
}

# Nukta-modified consonants — decomposed (base + U+09BC) handled as two-char sequences
_NUKTA_CONSONANTS: dict[str, str] = {
    "ড": "r",    # ড + ় → ড়  (rho)
    "ঢ": "rh",   # ঢ + ় → ঢ়
    "য": "y",    # য + ় → য়
}

# Special diacritics / modifiers
_SPECIALS: dict[str, str] = {
    "ং": "ng",   # anusvara (nasalization)
    "ঃ": "h",    # visarga
    "ঁ": "n",    # chandrabindu (nasal)
}

# Hasanta (virama) — suppresses inherent vowel between consonants
_HASANTA = "\u09CD"   # ্

# Bangla digits → ASCII
_DIGITS: dict[str, str] = {
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9",
}

# Bangla punctuation
_PUNCTUATION: dict[str, str] = {
    "।": ".",
    "॥": ".",
}

# Characters that signal a word boundary → suppress inherent 'o'
_WORD_BOUNDARY_CHARS = frozenset(" \t\n\r।॥!?.,;:\"'()/\\[]{}—–-")


def _is_word_boundary(ch: str | None) -> bool:
    """Return True if *ch* is a word-boundary character or end of string."""
    return ch is None or ch in _WORD_BOUNDARY_CHARS


# ---------------------------------------------------------------------------
# Core transliteration engine
# ---------------------------------------------------------------------------

def romanize(text: str, *, passthrough_non_bangla: bool = True) -> str:
    """
    Transliterate Bangla script characters in *text* to their Roman equivalents.

    Non-Bangla characters (Latin, digits, punctuation, etc.) are passed through
    unchanged when *passthrough_non_bangla* is True (default).

    Parameters
    ----------
    text : str
        Input string containing Bangla (and optionally other) script characters.
    passthrough_non_bangla : bool
        If True (default), non-Bangla characters are kept as-is.
        If False, non-Bangla characters are dropped from the output.

    Returns
    -------
    str
        Romanized string.

    Examples
    --------
    >>> romanize("বাংলা")
    'bangla'

    >>> romanize("আমি বাংলায় কথা বলি।")
    'ami banglay kotha boli.'

    >>> romanize("ঢাকা")
    'dhaka'

    >>> romanize("বাংলাদেশ")
    'bangladesh'

    >>> romanize("মুক্তিযুদ্ধ")
    'muktijuddho'

    >>> romanize("আমি English মিশিয়ে বলি")
    'ami English mishiye boli'
    """
    # NFC normalization consolidates precomposed forms (ড়, ঢ়, য় → single codepoints)
    text = unicodedata.normalize("NFC", text)

    chars = list(text)
    result: list[str] = []
    i = 0
    n = len(chars)

    while i < n:
        ch = chars[i]
        peek  = chars[i + 1] if i + 1 < n else None
        peek2 = chars[i + 2] if i + 2 < n else None

        # --- Consonant + nukta (decomposed ড়/ঢ়/য়) —check BEFORE plain consonant ---
        if ch in _NUKTA_CONSONANTS and peek == _NUKTA:
            roman = _NUKTA_CONSONANTS[ch]
            after_nukta = chars[i + 2] if i + 2 < n else None
            if after_nukta == _HASANTA:
                result.append(roman)
                i += 3   # consonant + nukta + hasanta
            elif after_nukta in _MATRAS:
                result.append(roman + _MATRAS[after_nukta])
                i += 3   # consonant + nukta + matra
            else:
                # Inherent 'o' — suppress at word boundary
                inherent = "" if _is_word_boundary(after_nukta) else "o"
                result.append(roman + inherent)
                i += 2   # consonant + nukta (after_nukta handled next iteration)

        # --- Plain consonant ---
        elif ch in _CONSONANTS:
            roman = _CONSONANTS[ch]
            if peek == _HASANTA:
                result.append(roman)
                i += 2
            elif peek in _MATRAS:
                result.append(roman + _MATRAS[peek])
                i += 2
            else:
                # Suppress inherent 'o' at word boundary (space / end of string)
                inherent = "" if _is_word_boundary(peek) else "o"
                result.append(roman + inherent)
                i += 1

        # --- Independent vowel ---
        elif ch in _VOWELS:
            result.append(_VOWELS[ch])
            i += 1

        # --- Orphan matra (shouldn't appear in well-formed text) ---
        elif ch in _MATRAS:
            result.append(_MATRAS[ch])
            i += 1

        # --- Anusvara / visarga / chandrabindu ---
        elif ch in _SPECIALS:
            result.append(_SPECIALS[ch])
            i += 1

        # --- Standalone nukta (not after a nukta-consonant — edge case) ---
        elif ch == _NUKTA:
            i += 1   # skip

        # --- Hasanta without preceding consonant (edge case) ---
        elif ch == _HASANTA:
            i += 1

        # --- Bangla digits ---
        elif ch in _DIGITS:
            result.append(_DIGITS[ch])
            i += 1

        # --- Bangla punctuation ---
        elif ch in _PUNCTUATION:
            result.append(_PUNCTUATION[ch])
            i += 1

        # --- Non-Bangla character ---
        else:
            if passthrough_non_bangla:
                result.append(ch)
            i += 1

    return "".join(result)


def romanize_word(word: str) -> str:
    """
    Romanize a single Bangla word token.

    Convenience wrapper around :func:`romanize` that strips whitespace
    before and after processing.

    Examples
    --------
    >>> romanize_word("বাংলাদেশ")
    'bangladesh'
    """
    return romanize(word.strip())


def romanize_tokens(tokens: list[str]) -> list[str]:
    """
    Romanize a list of word tokens in-place.

    Parameters
    ----------
    tokens : list[str]
        List of string tokens (as produced by :func:`bangla_nlpkit.tokenizer.word_tokenize`).

    Returns
    -------
    list[str]
        New list with each token romanized.

    Examples
    --------
    >>> romanize_tokens(["আমি", "বাংলায়", "কথা", "বলি"])
    ['ami', 'banglay', 'kotha', 'boli']
    """
    return [romanize(token) for token in tokens]