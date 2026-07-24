"""
tokenizer.py — Word and sentence tokenization for Bangla text.

Handles:
  - Bangla-specific sentence endings (danda ।, double danda ॥)
  - Mixed Bangla-English text
  - Bangla, Latin, Arabic, Devanagari, Chakma, Myanmar script blocks
  - Punctuation separation without splitting within words
"""

from __future__ import annotations
import re


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# All Unicode script ranges we want to keep as atomic token chunks
_SCRIPT_BLOCKS = (
    r"[\u0980-\u09FF]+"   # Bangla
    r"|[\u0900-\u097F]+"  # Devanagari
    r"|[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]+"  # Arabic
    r"|[A-Za-z\u00C0-\u00FF]+"   # Latin (incl. extended)
    r"|[\u11100-\u1114F]+"       # Chakma
    r"|[\u1000-\u109F]+"         # Myanmar (Marma)
    r"|[0-9০-৯]+"               # Digits (ASCII + Bangla)
)

# Bangla sentence delimiters and standard endings
_SENTENCE_SPLITTER = re.compile(
    r"(?<=[।॥!?])\s*"       # after danda / double danda / ! / ?
    r"|(?<=\.{1})\s+"        # after period followed by whitespace
    r"|(?<=\n)\s*"           # after newline
)

# Tokenizer: match script blocks OR single non-whitespace punctuation
_WORD_RE = re.compile(_SCRIPT_BLOCKS + r"|[^\s]", re.UNICODE)

# Sentence boundary punctuation pattern (used in span-based sentence tokenizer)
_SENT_BOUNDARY_RE = re.compile(
    r"[।॥]"              # Bangla danda / double danda
    r"|[!?]+"            # exclamation / question marks
    r"|\.(?!\d)"         # period not followed by digit (avoid splitting "3.14")
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def word_tokenize(text: str, *, keep_punctuation: bool = False) -> list[str]:
    """
    Tokenize *text* into words, handling Bangla, Latin, Arabic, and mixed text.

    Parameters
    ----------
    text : str
        Input string.
    keep_punctuation : bool
        If True, punctuation marks are included as separate tokens.
        If False (default), only script-block tokens and digit tokens are returned.

    Returns
    -------
    list[str]
        List of word tokens.

    Examples
    --------
    >>> word_tokenize("আমি বাংলায় কথা বলি।")
    ['আমি', 'বাংলায়', 'কথা', 'বলি']

    >>> word_tokenize("আমি English মিশিয়ে বলি!")
    ['আমি', 'English', 'মিশিয়ে', 'বলি']

    >>> word_tokenize("আমার বয়স ২৩।", keep_punctuation=True)
    ['আমার', 'বয়স', '২৩', '।']
    """
    tokens = _WORD_RE.findall(text)
    if keep_punctuation:
        return tokens
    # Filter out tokens that are purely punctuation / symbols
    return [t for t in tokens if re.search(r"[\w\u0980-\u09FF\u0600-\u06FF]", t)]


def sentence_tokenize(text: str) -> list[str]:
    """
    Split *text* into sentences, respecting Bangla danda (।) and double danda (॥).

    Parameters
    ----------
    text : str
        Input paragraph or multi-sentence string.

    Returns
    -------
    list[str]
        List of sentence strings (stripped, non-empty).

    Examples
    --------
    >>> sentence_tokenize("আমি বাংলায় কথা বলি। তুমি কি বাংলায় কথা বলো?")
    ['আমি বাংলায় কথা বলি।', 'তুমি কি বাংলায় কথা বলো?']

    >>> sentence_tokenize("She said hello. He replied hi! Then they left.")
    ['She said hello.', 'He replied hi!', 'Then they left.']
    """
    if not text.strip():
        return []

    # Walk through text and split on sentence boundaries
    sentences: list[str] = []
    last = 0

    for m in _SENT_BOUNDARY_RE.finditer(text):
        end = m.end()
        # Grab from last position up to and including the boundary punctuation
        chunk = text[last:end].strip()
        if chunk:
            sentences.append(chunk)
        # Skip whitespace after the boundary
        rest = text[end:]
        skip = len(rest) - len(rest.lstrip())
        last = end + skip

    # Append any trailing text that had no closing punctuation
    tail = text[last:].strip()
    if tail:
        sentences.append(tail)

    return sentences


def char_tokenize(text: str) -> list[str]:
    """
    Tokenize *text* into individual characters (useful for character-level models).

    Parameters
    ----------
    text : str
        Input string.

    Returns
    -------
    list[str]
        List of individual characters, excluding whitespace.

    Examples
    --------
    >>> char_tokenize("বাংলা")
    ['ব', 'া', 'ং', 'ল', 'া']
    """
    return [ch for ch in text if not ch.isspace()]