"""
bangla-nlpkit
=============

A lightweight Python toolkit for Bangla (Bengali) NLP tasks, with support
for Chakma, Myanmar (Marma), Devanagari, Arabic, and Latin scripts.

Quick start
-----------
>>> from bangla_nlpkit import detect_script, normalize, word_tokenize, romanize
>>> detect_script("আমি বাংলায় কথা বলি").dominant
'bangla'
>>> normalize("  আমি  বাংলায়  কথা  বলি  ")
'আমি বাংলায় কথা বলি'
>>> word_tokenize("আমি বাংলায় কথা বলি।")
['আমি', 'বাংলায়', 'কথা', 'বলি']
>>> romanize("বাংলাদেশ")
'bangladesh'
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("bangla-nlpkit")
except PackageNotFoundError:  # running from source without install
    __version__ = "0.1.0"

# Script detection
from bangla_nlpkit.detector import (
    detect_script,
    is_bangla,
    DetectionResult,
)

# Unicode normalization
from bangla_nlpkit.normalizer import (
    normalize,
    to_ascii_digits,
    to_bangla_digits,
    remove_invisible,
)

# Tokenization
from bangla_nlpkit.tokenizer import (
    word_tokenize,
    sentence_tokenize,
    char_tokenize,
)

# Romanization
from bangla_nlpkit.romanizer import (
    romanize,
    romanize_word,
    romanize_tokens,
)

__all__ = [
    # detection
    "detect_script",
    "is_bangla",
    "DetectionResult",
    # normalization
    "normalize",
    "to_ascii_digits",
    "to_bangla_digits",
    "remove_invisible",
    # tokenization
    "word_tokenize",
    "sentence_tokenize",
    "char_tokenize",
    # romanization
    "romanize",
    "romanize_word",
    "romanize_tokens",
]