"""
benchmark_romanizer.py

Compares bangla-nlpkit's deterministic ASCII romanizer against
indic_transliteration (ISO 15919 scheme) — the established rule-based
baseline for Bengali transliteration.

IMPORTANT SCOPE NOTE:
This benchmark does NOT use BanglaTLit (Fahim et al., EMNLP 2024 Findings),
because BanglaTLit is a Roman->Bangla back-transliteration dataset built
from informal social-media Banglish, which is a fundamentally different
task (one-to-many, register-dependent, requires a trained model to
approximate). Benchmarking a deterministic Bangla->Roman formal
transliterator against that data would be an invalid comparison.

Instead, this benchmark evaluates on:
  1. A curated formal-register test set (place names, dictionary words,
     common phrases) covering known hard cases: word-final consonants,
     conjuncts, decomposed nukta characters, matras.
  2. Structural correctness checks (does each system produce valid,
     complete output with no dropped characters).
  3. Practical engineering metrics: dependency footprint, install size,
     import/runtime speed — relevant because bangla-nlpkit targets
     lightweight/offline/embedded use cases.
"""

import time

from bangla_nlpkit.romanizer import romanize as bnk_romanize

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as iso_transliterate


# ---------------------------------------------------------------------------
# Curated formal-register test set
# Covers: place names, common dictionary words, the specific bug classes
# bangla-nlpkit fixed (word-final inherent vowel, decomposed nukta),
# and general sentences.
# ---------------------------------------------------------------------------

TEST_CASES = [
    # (Bengali, category, notes)
    ("বাংলাদেশ", "place_name", "word-final consonant — must suppress inherent vowel"),
    ("ঢাকা", "place_name", "standard place name"),
    ("চট্টগ্রাম", "place_name", "conjunct consonant cluster"),
    ("সিলেট", "place_name", "word-final consonant"),
    ("রাজশাহী", "place_name", "long vowel + word-final"),
    ("বাংলা", "common_word", "basic word"),
    ("মুক্তিযুদ্ধ", "common_word", "double conjunct, hasanta chain"),
    ("বিশ্ববিদ্যালয়", "common_word", "decomposed য় (nukta), long word"),
    ("গবেষণা", "common_word", "retroflex consonants"),
    ("ভাষা", "common_word", "sibilant"),
    ("আমি বাংলায় কথা বলি", "sentence", "decomposed য় mid-sentence"),
    ("আমার নাম রাশেদুল", "sentence", "personal name, word-final"),
    ("বাংলাদেশ একটি সুন্দর দেশ", "sentence", "full sentence, multiple word-finals"),
]


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate via Levenshtein distance, normalized by ref length."""
    ref, hyp = reference, hypothesis
    m, n = len(ref), len(hyp)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )
    return dp[m][n] / max(1, len(ref))


def strip_diacritics(text: str) -> str:
    """Rough ASCII-fold of ISO 15919 diacritics for structural comparison only."""
    mapping = {
        "ā": "a", "ī": "i", "ū": "u", "ē": "e", "ō": "o",
        "ṁ": "ng", "ḥ": "h", "ṅ": "ng", "ñ": "ny",
        "ṭ": "t", "ḍ": "d", "ṇ": "n", "ś": "sh", "ṣ": "sh",
        "়": "", "্": "",
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text


def run_correctness_benchmark():
    print("=" * 100)
    print("PART 1 — STRUCTURAL CORRECTNESS ON CURATED FORMAL-REGISTER TEST SET")
    print("=" * 100)
    print(f"{'Bengali':<20}{'bangla-nlpkit':<22}{'indic_translit (ISO)':<24}{'ISO->ASCII-fold':<20}{'CER (bnk vs fold)':<10}")
    print("-" * 100)

    total_cer = 0.0
    n = len(TEST_CASES)

    results = []
    for bengali, category, note in TEST_CASES:
        bnk_out = bnk_romanize(bengali)
        iso_out = iso_transliterate(bengali, sanscript.BENGALI, sanscript.ISO)
        iso_folded = strip_diacritics(iso_out)
        c = cer(iso_folded, bnk_out)
        total_cer += c
        results.append((bengali, bnk_out, iso_out, iso_folded, c, category, note))
        print(f"{bengali:<20}{bnk_out:<22}{iso_out:<24}{iso_folded:<20}{c:.3f}")

    print("-" * 100)
    print(f"Mean CER (bangla-nlpkit vs. diacritic-folded ISO 15919): {total_cer/n:.3f}")
    print()
    print("Interpretation: CER here measures STRUCTURAL agreement between two")
    print("different transliteration philosophies (ASCII-practical vs. academic-ISO),")
    print("not 'accuracy' — there is no single ground truth. Divergences are expected")
    print("and mostly reflect scheme design choices (e.g., vowel length marking,")
    print("retroflex marking), not errors. Full case-by-case notes below.")
    print()

    for bengali, bnk_out, iso_out, iso_folded, c, category, note in results:
        print(f"  [{category}] {bengali} — {note}")
        print(f"    bangla-nlpkit : {bnk_out}")
        print(f"    ISO 15919     : {iso_out}")
        print()


def run_edge_case_regression():
    """
    Re-runs the two specific bugs bangla-nlpkit fixed, and checks whether
    indic_transliteration exhibits the same failure modes.
    """
    print("=" * 100)
    print("PART 2 — EDGE CASE REGRESSION (bugs bangla-nlpkit specifically fixed)")
    print("=" * 100)

    cases = [
        ("বাংলাদেশ", "bangladesh", "word-final inherent vowel suppression"),
        ("বিশ্ববিদ্যালয়", None, "decomposed nukta (য় = য + ়)"),
    ]

    for bengali, expected, description in cases:
        bnk_out = bnk_romanize(bengali)
        iso_out = iso_transliterate(bengali, sanscript.BENGALI, sanscript.ISO)
        print(f"\n{description}")
        print(f"  Input          : {bengali}")
        print(f"  bangla-nlpkit  : {bnk_out}" + (f"  {'✓ correct' if expected and bnk_out == expected else ''}"))
        print(f"  ISO 15919      : {iso_out}")


def run_footprint_benchmark():
    print()
    print("=" * 100)
    print("PART 3 — ENGINEERING FOOTPRINT (relevant for offline/embedded/CLI use)")
    print("=" * 100)

    # Install size (measured earlier via du/os.walk)
    print(f"{'Metric':<35}{'bangla-nlpkit':<20}{'indic_transliteration':<25}")
    print("-" * 80)
    print(f"{'Runtime dependencies':<35}{'0':<20}{'6 (regex, roman, toml, tqdm, typer, backports)':<25}")
    print(f"{'Package size (installed)':<35}{'~40 KB':<20}{'~390 KB':<25}")

    # Speed test — romanize 1000 sentences
    text = "আমি বাংলায় কথা বলি। " * 1
    iterations = 1000

    start = time.perf_counter()
    for _ in range(iterations):
        bnk_romanize(text)
    bnk_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iterations):
        iso_transliterate(text, sanscript.BENGALI, sanscript.ISO)
    iso_time = time.perf_counter() - start

    print(f"{'Time for 1000 calls (sec)':<35}{bnk_time:<20.4f}{iso_time:<25.4f}")
    print(f"{'Relative speed':<35}{'1.0x (baseline)':<20}{f'{iso_time/bnk_time:.1f}x slower' if iso_time > bnk_time else f'{bnk_time/iso_time:.1f}x faster':<25}")


if __name__ == "__main__":
    run_correctness_benchmark()
    run_edge_case_regression()
    run_footprint_benchmark()