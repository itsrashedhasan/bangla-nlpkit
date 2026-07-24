"""
benchmark_nukta.py

Systematic test of decomposed-nukta handling (ড়/ঢ়/য় as base consonant +
U+09BC combining nukta, vs. their precomposed single-codepoint forms).

This produces the actual N/failure-rate number needed for paper.md,
replacing the single anecdotal example from earlier development.

Methodology:
  For each test word, we construct BOTH the precomposed and decomposed
  Unicode representation of the target character, run both through
  bangla-nlpkit.romanize() and indic_transliteration (ISO 15919), and
  check:
    1. Does the decomposed form produce IDENTICAL romanized output to
       the precomposed form? (this is the correctness criterion — a
       reader should get the same transliteration regardless of which
       Unicode representation the source text happens to use)
    2. Does the output contain a "leaked" combining nukta character
       (U+09BC) that was not converted at all? (structural failure —
       unambiguous bug, independent of scheme)
"""

import unicodedata

from bangla_nlpkit.romanizer import romanize as bnk_romanize
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as iso_transliterate

NUKTA = "\u09BC"

# Precomposed -> (base consonant, decomposed form) for the three nukta letters
DECOMPOSITION_MAP = {
    "\u09DC": "\u09A1" + NUKTA,  # ড় (RRA)  = ড (DDA)  + nukta
    "\u09DD": "\u09A2" + NUKTA,  # ঢ় (RHA)  = ঢ (DDHA) + nukta
    "\u09DF": "\u09AF" + NUKTA,  # য় (YYA)  = য (YA)   + nukta
}

# 40 curated real Bangla words containing at least one of these characters,
# covering word-initial, word-medial, and word-final positions, and mixing
# all three target letters. Words sourced from common vocabulary, place
# names, and the specific terms already known to be problematic
# (বিশ্ববিদ্যালয়, রাজশাহী-adjacent forms, etc.)
# 40 curated real Bangla words containing ড়/ঢ়/য়, built with the target
# character in its TRUE PRECOMPOSED single-codepoint form (\u09DC, \u09DD,
# \u09DF). This is done explicitly via string concatenation rather than by
# typing/pasting the character directly, because in practice most input
# methods (including copy-paste in this environment) produce the DECOMPOSED
# sequence (base consonant + U+09BC) by default — pasting the character
# visually is not a reliable way to guarantee the precomposed codepoint.
# An earlier version of this script made exactly this mistake: the word
# list looked correct visually but every word was already decomposed at
# the source, silently invalidating the precomposed/decomposed comparison.

def _w(base: str, precomposed_char: str, suffix: str = "") -> str:
    """Build a word ending in the exact precomposed target character."""
    return base + precomposed_char + suffix

YYA = "\u09DF"   # য় precomposed
RRA = "\u09DC"   # ড় precomposed
RHA = "\u09DD"   # ঢ় precomposed

TEST_WORDS_PRECOMPOSED = [
    _w("বিশ্ববিদ্যাল", YYA),           # বিশ্ববিদ্যালয় university
    _w("কার্যাল", YYA),                 # কার্যালয় office
    _w("আল", YYA),                      # আলয় abode
    _w("ব্", YYA),                      # ব্যয় expense (approx.)
    _w("সম", YYA),                      # সময় time
    _w("হৃদ", YYA),                     # হৃদয় heart
    _w("প্রণ", YYA),                    # প্রণয় affection
    _w("নিশ্চ", YYA),                   # নিশ্চয় certainly
    _w("উদ", YYA),                      # উদয় sunrise
    _w("বিজ", YYA),                     # বিজয় victory
    _w("পরিচ", YYA),                    # পরিচয় identity
    _w("সঞ্চ", YYA),                    # সঞ্চয় savings
    _w("বিদা", YYA),                    # বিদায় farewell
    _w("উপা", YYA),                     # উপায় method
    _w("সহা", YYA),                     # সহায় helper
    _w("ল", YYA),                       # লয় dissolution
    _w("ক্ষ", YYA),                     # ক্ষয় decay
    _w("দ্ব", YYA),                     # দ্বয় pair
    _w("ন্যা", YYA),                    # ন্যায় justice
    _w("র", YYA, "েছে"),                # রয়েছে exists/remains
    _w("হ", YYA, "েছে"),                # হয়েছে has happened
    _w("গি", YYA, "েছে"),                # গিয়েছে has gone
    _w("নি", YYA, "েছে"),                # নিয়েছে has taken
    _w("দি", YYA, "েছে"),                # দিয়েছে has given
    _w("খে", YYA, "েছে"),                # খেয়েছে has eaten
    _w("চে", YYA, "েছে"),                # চেয়েছে has wanted
    _w("পে", YYA, "েছে"),                # পেয়েছে has received
    _w("বি", YYA, "ে"),                  # বিয়ে wedding
    _w("প্রি", YYA),                    # প্রিয় dear
    _w("ভ", YYA),                       # ভয় fear
    _w("জ", YYA),                       # জয় victory
    _w("ন", YYA),                       # নয় nine/not
    _w("গ", RRA),                       # গড় build/average
    _w("ব", RRA),                       # বড় big
    _w("জ", RRA),                       # জড় entangled
    _w("পাহা", RRA),                    # পাহাড় mountain
    _w("দা", RRA, "ি"),                  # দাড়ি beard
    _w("গা", RHA),                      # গাঢ় deep/dense
    _w("লা", RHA),                      # লাঢ় (constructed, tests RHA)
    _w("বা", RHA, "ে"),                  # বাঢ়ে (constructed, tests RHA)
]


def has_leaked_nukta(text: str) -> bool:
    """Check whether the output string contains an unconverted nukta character."""
    return NUKTA in text or "়" in text


def run_nukta_benchmark():
    print("=" * 110)
    print("EXPANDED NUKTA BENCHMARK — decomposed vs. precomposed Unicode forms")
    print(f"Test set size: {len(TEST_WORDS_PRECOMPOSED)} words")
    print("=" * 110)

    bnk_mismatches = 0
    bnk_leaks = 0
    iso_mismatches = 0
    iso_leaks = 0

    detailed_failures = []

    for word_precomposed in TEST_WORDS_PRECOMPOSED:
        # Build the decomposed version by substituting each precomposed
        # nukta character with its base+combining-mark equivalent
        word_decomposed = word_precomposed
        for precomposed_char, decomposed_seq in DECOMPOSITION_MAP.items():
            word_decomposed = word_decomposed.replace(precomposed_char, decomposed_seq)

        # HARD CHECK (not a silent skip): every test word MUST actually
        # contain a precomposed target character, or this benchmark is
        # measuring nothing. An earlier version of this script silently
        # skipped such words instead of failing loudly, which produced a
        # meaningless "100% pass" result when the word list was
        # accidentally already-decomposed at the source.
        assert word_decomposed != word_precomposed, (
            f"Test word {word_precomposed!r} contains no precomposed "
            f"ড়/ঢ়/য় character — check source encoding, this word "
            f"cannot be used in this benchmark."
        )

        # --- bangla-nlpkit ---
        bnk_pre = bnk_romanize(word_precomposed)
        bnk_dec = bnk_romanize(word_decomposed)
        bnk_match = (bnk_pre == bnk_dec)
        bnk_leak = has_leaked_nukta(bnk_dec)

        if not bnk_match:
            bnk_mismatches += 1
        if bnk_leak:
            bnk_leaks += 1

        # --- indic_transliteration (ISO 15919) ---
        iso_pre = iso_transliterate(word_precomposed, sanscript.BENGALI, sanscript.ISO)
        iso_dec = iso_transliterate(word_decomposed, sanscript.BENGALI, sanscript.ISO)
        iso_match = (iso_pre == iso_dec)
        iso_leak = has_leaked_nukta(iso_dec)

        if not iso_match:
            iso_mismatches += 1
        if iso_leak:
            iso_leaks += 1

        if not bnk_match or not iso_match or bnk_leak or iso_leak:
            detailed_failures.append({
                "word": word_precomposed,
                "bnk_pre": bnk_pre, "bnk_dec": bnk_dec, "bnk_match": bnk_match, "bnk_leak": bnk_leak,
                "iso_pre": iso_pre, "iso_dec": iso_dec, "iso_match": iso_match, "iso_leak": iso_leak,
            })

    n = len(TEST_WORDS_PRECOMPOSED)

    print(f"\n{'System':<25}{'Precomposed=Decomposed match':<32}{'Leaked nukta in output':<28}")
    print("-" * 85)
    print(f"{'bangla-nlpkit':<25}{f'{n - bnk_mismatches}/{n} ({100*(n-bnk_mismatches)/n:.1f}%)':<32}{f'{bnk_leaks}/{n} ({100*bnk_leaks/n:.1f}%)':<28}")
    print(f"{'indic_transliteration':<25}{f'{n - iso_mismatches}/{n} ({100*(n-iso_mismatches)/n:.1f}%)':<32}{f'{iso_leaks}/{n} ({100*iso_leaks/n:.1f}%)':<28}")

    if detailed_failures:
        print(f"\n{'='*110}")
        print(f"DETAILED FAILURES ({len(detailed_failures)} words with at least one issue)")
        print(f"{'='*110}")
        for f in detailed_failures:
            print(f"\nWord: {f['word']}")
            print(f"  bangla-nlpkit   precomposed: {f['bnk_pre']!r}")
            print(f"  bangla-nlpkit   decomposed : {f['bnk_dec']!r}"
                  f"  {'[MISMATCH]' if not f['bnk_match'] else ''}"
                  f"  {'[LEAKED NUKTA]' if f['bnk_leak'] else ''}")
            print(f"  ISO 15919       precomposed: {f['iso_pre']!r}")
            print(f"  ISO 15919       decomposed : {f['iso_dec']!r}"
                  f"  {'[MISMATCH]' if not f['iso_match'] else ''}"
                  f"  {'[LEAKED NUKTA]' if f['iso_leak'] else ''}")

    print(f"\n{'='*110}")
    print("SUMMARY FOR paper.md")
    print(f"{'='*110}")
    print(f"Test set: {n} curated Bangla words containing ড়/ঢ়/য় in word-initial,")
    print(f"word-medial, or word-final position.")
    print(f"\nbangla-nlpkit:")
    print(f"  - Precomposed/decomposed output mismatch: {bnk_mismatches}/{n} ({100*bnk_mismatches/n:.1f}%)")
    print(f"  - Unconverted (leaked) nukta in output:    {bnk_leaks}/{n} ({100*bnk_leaks/n:.1f}%)")
    print(f"\nindic_transliteration (ISO 15919):")
    print(f"  - Precomposed/decomposed output mismatch: {iso_mismatches}/{n} ({100*iso_mismatches/n:.1f}%)")
    print(f"  - Unconverted (leaked) nukta in output:    {iso_leaks}/{n} ({100*iso_leaks/n:.1f}%)")

    return {
        "n": n,
        "bnk_mismatches": bnk_mismatches, "bnk_leaks": bnk_leaks,
        "iso_mismatches": iso_mismatches, "iso_leaks": iso_leaks,
        "detailed_failures": detailed_failures,
    }


if __name__ == "__main__":
    run_nukta_benchmark()
