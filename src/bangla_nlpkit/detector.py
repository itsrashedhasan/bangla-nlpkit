"""
detector.py — Script detection for Bangla and related languages.

Detects dominant script(s) in a string using Unicode range analysis.
Supports: Bangla, Latin, Arabic, Devanagari, Chakma, Myanmar (Marma).

Note: Garo language uses Latin script, so Garo text will be detected
as 'latin'. Use language-level models for Garo vs English disambiguation.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


# ---------------------------------------------------------------------------
# Unicode script ranges
# Each entry: name → list of (start, end) inclusive ranges
# ---------------------------------------------------------------------------
_SCRIPT_RANGES: Dict[str, list[tuple[int, int]]] = {
    "bangla":      [(0x0980, 0x09FF)],
    "devanagari":  [(0x0900, 0x097F)],
    "arabic":      [(0x0600, 0x06FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    "latin":       [(0x0041, 0x005A), (0x0061, 0x007A),
                    (0x00C0, 0x00D6), (0x00D8, 0x00F6), (0x00F8, 0x00FF)],
    "chakma":      [(0x11100, 0x1114F)],
    "myanmar":     [(0x1000, 0x109F)],   # Used by Marma community
}

_SCRIPT_ORDER = ["bangla", "latin", "arabic", "devanagari", "chakma", "myanmar"]


def _classify_char(ch: str) -> str | None:
    """Return the script name for a single character, or None if unclassified."""
    cp = ord(ch)
    for script in _SCRIPT_ORDER:
        for start, end in _SCRIPT_RANGES[script]:
            if start <= cp <= end:
                return script
    return None


@dataclass
class DetectionResult:
    """Result of script detection on a text string."""
    dominant: str
    """The most frequent script found ('bangla', 'latin', 'arabic', etc.)
    Returns 'unknown' if no classifiable characters are found."""
    scores: Dict[str, float]
    """Proportion of classifiable characters belonging to each script (0.0–1.0)."""
    char_counts: Dict[str, int]
    """Raw character counts per script."""
    total_classified: int
    """Total number of characters that were classified into a script."""

    def is_mixed(self, threshold: float = 0.15) -> bool:
        """Return True if more than one script exceeds the threshold proportion."""
        above = sum(1 for v in self.scores.values() if v >= threshold)
        return above > 1

    def __repr__(self) -> str:
        parts = ", ".join(f"{k}={v:.2f}" for k, v in self.scores.items() if v > 0)
        return f"DetectionResult(dominant='{self.dominant}', scores={{ {parts} }})"


def detect_script(text: str) -> DetectionResult:
    """
    Detect the script(s) present in *text*.

    Parameters
    ----------
    text : str
        Input string (may be Bangla, English, Arabic, mixed, etc.)

    Returns
    -------
    DetectionResult
        Contains the dominant script name, per-script proportions,
        raw counts, and total classified character count.

    Examples
    --------
    >>> detect_script("আমি বাংলায় কথা বলি")
    DetectionResult(dominant='bangla', scores={ bangla=1.00 })

    >>> detect_script("Hello world")
    DetectionResult(dominant='latin', scores={ latin=1.00 })

    >>> detect_script("আমি English মিশিয়ে বলি")
    DetectionResult(dominant='bangla', scores={ bangla=0.67, latin=0.33 })
    """
    counts: Dict[str, int] = {s: 0 for s in _SCRIPT_RANGES}

    for ch in text:
        script = _classify_char(ch)
        if script:
            counts[script] += 1

    total = sum(counts.values())

    if total == 0:
        return DetectionResult(
            dominant="unknown",
            scores={s: 0.0 for s in counts},
            char_counts=counts,
            total_classified=0,
        )

    scores = {s: round(c / total, 4) for s, c in counts.items()}
    dominant = max(counts, key=counts.get)  # type: ignore[arg-type]

    return DetectionResult(
        dominant=dominant,
        scores=scores,
        char_counts=counts,
        total_classified=total,
    )


def is_bangla(text: str, min_ratio: float = 0.5) -> bool:
    """
    Return True if *text* is predominantly Bangla script.

    Parameters
    ----------
    text : str
        Input string.
    min_ratio : float
        Minimum proportion of Bangla characters required (default 0.5).

    Examples
    --------
    >>> is_bangla("আমি বাংলায় কথা বলি")
    True
    >>> is_bangla("Hello world")
    False
    """
    result = detect_script(text)
    return result.scores.get("bangla", 0.0) >= min_ratio