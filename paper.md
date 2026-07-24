---
title: 'bangla-nlpkit: A Zero-Dependency Toolkit for Bangla Script Detection, Normalization, Tokenization, and Romanization'
tags:
  - Python
  - natural language processing
  - Bangla
  - Bengali
  - low-resource languages
  - transliteration
  - Unicode
authors:
  - name: Rashedul Hasan Shohan
    orcid: 0009-0004-9069-484X
    affiliation: 1
affiliations:
  - name: Department of Computer Science and Engineering, Daffodil International University, Dhaka, Bangladesh
    index: 1
date: TODO — set on submission
bibliography: paper.bib
---

# Summary

`bangla-nlpkit` is a lightweight, dependency-free Python library for
preprocessing Bangla (Bengali) text. It provides four core capabilities:
script detection across six Unicode script families (Bangla, Latin, Arabic,
Devanagari, Chakma, and Myanmar), Unicode normalization tailored to known
Bangla-specific encoding issues, word/sentence tokenization that respects
Bangla-specific punctuation (danda `।` and double danda `॥`), and a
deterministic, phonetically-tuned Bangla-to-Roman transliteration scheme. The
library targets researchers and developers who need reliable Bangla text
preprocessing without pulling in heavyweight machine-learning dependencies
(embeddings, pretrained models, or GPU-backed tokenizers), making it suitable
for offline, embedded, and low-resource deployment contexts.

# Statement of need

Bangla is spoken by roughly 250 million people and is classified as a
low-resource language in NLP tooling despite its speaker population
[@bnlp2021]. Existing Bangla NLP toolkits such as `bnlp-toolkit`
[@bnlp2021], `bltk`, and `bnltk` provide substantial functionality —
tokenization, word embeddings, POS tagging, and named entity recognition —
but rely on pretrained models and dependencies such as `gensim`, `fasttext`,
and `sentencepiece`. This makes them poorly suited to lightweight, offline,
or embedded use cases, and introduces model-versioning and download
dependencies that complicate reproducibility.

`bangla-nlpkit` addresses a narrower but distinct need: a **zero-dependency**,
**deterministic**, rule-based toolkit for the preprocessing stage of a Bangla
NLP pipeline. In particular, its romanization module addresses two specific,
verifiable Unicode-handling defects common in naive Bangla-to-Roman
transliteration implementations:

1. **Word-final inherent-vowel suppression.** Bangla is an abugida in which
   consonants carry an inherent vowel unless followed by a vowel diacritic
   (matra) or a virama (hasanta, `্`). Many transliteration schemes fail to
   suppress this inherent vowel at word boundaries, producing incorrect
   output (e.g. rendering বাংলাদেশ as `bangladesho` rather than
   `bangladesh`). `bangla-nlpkit` explicitly detects word boundaries
   (whitespace, punctuation, end-of-string) and suppresses the inherent
   vowel accordingly.

2. **Decomposed nukta handling.** The characters ড়, ঢ়, and য় may appear
   in Unicode Bangla text either as single precomposed code points or as a
   base consonant (ড, ঢ, য) followed by a combining nukta mark (U+09BC).
   Critically, these two forms are canonically decomposition-equivalent but
   are excluded from Unicode canonical *composition* (they appear on the
   Unicode Composition Exclusion Table), meaning standard NFC normalization
   will never recompose a decomposed sequence back to its precomposed form.
   Any implementation that relies on NFC normalization to unify these two
   input forms will therefore systematically fail on decomposed input. We
   verified this empirically on a curated set of 40 Bangla words containing
   ড়/ঢ়/য় in word-initial, word-medial, and word-final position (built
   from explicit Unicode code points to guarantee correct precomposed
   source forms). `bangla-nlpkit` produced identical romanization output
   for the precomposed and decomposed form of every word (40/40, 100%),
   with no leaked, unconverted nukta characters in any output. By contrast,
   `indic_transliteration` (ISO 15919) — a maintained, widely used Python
   package — produced a mismatched, corrupted output containing an
   unconverted nukta character for every single decomposed-form input
   (40/40, 100%). The benchmark script and full per-word results are
   available in `benchmarks/benchmark_nukta.py`.

# Comparison to existing tools

We benchmarked `bangla-nlpkit` against `indic_transliteration`, a maintained
Python package implementing the ISO 15919 pan-Indic romanization standard,
on a curated set of 40 Bangla words containing decomposed-nukta characters
(ড়/ঢ়/য়) in word-initial, medial, and final position. `bangla-nlpkit`
produced consistent, uncorrupted output regardless of whether the input
used the precomposed or decomposed Unicode form of these characters
(40/40 words, 100% consistency, 0% leaked nukta characters). By contrast,
`indic_transliteration` produced corrupted output — containing an
unconverted, leaked nukta character — on every decomposed-form input in
the test set (40/40, 100% failure rate). Full per-word results, including
both systems' output on both Unicode forms, are provided in
`benchmarks/benchmark_nukta.py` and its accompanying results table.

We additionally note that `bangla-nlpkit`'s romanization output differs
systematically from ISO 15919 in a separate, non-error way: ISO 15919 is a
pan-Indic scheme derived primarily from Sanskrit/Devanagari transliteration
conventions and renders ব as `v` (reflecting Devanagari व), whereas
`bangla-nlpkit` renders ব as `b`, matching its phonetic realization in
spoken Bangla. This is documented as a design difference between two
transliteration philosophies (academic/reversible vs. practical/ASCII),
not framed as a superiority claim.

Engineering-footprint comparison against `indic_transliteration` shows
`bangla-nlpkit` has zero runtime dependencies versus six
(`regex`, `roman`, `toml`, `tqdm`, `typer`, `backports.functools_lru_cache`),
and an installed package size of approximately 40 KB versus approximately
390 KB. A controlled latency benchmark (10 independent trials of 20,000
calls each on a fixed input sentence, with a discarded warm-up trial,
measured using `time.perf_counter()`) was independently run on two
platforms:

| Platform | bangla-nlpkit (median µs/call) | indic_transliteration (median µs/call) | Ratio |
|---|---|---|---|
| Linux, Python 3.12.3, x86_64 | 11.75 (± 1.1% rel. stdev) | 57.08 (± 1.3% rel. stdev) | 4.86x |
| Windows 10, Python 3.12.6, Intel64 | 35.01 (± 4.2% rel. stdev) | 145.81 (± 1.3% rel. stdev) | 4.16x |

Both platforms independently show `bangla-nlpkit` approximately 4-5x
faster per call, with all measurements falling within acceptable relative
variance (under 5%). Absolute latencies differ between platforms as
expected (different hardware and OS scheduling behavior), but the relative
performance ratio is consistent, indicating the speed difference reflects
a genuine property of the two implementations rather than measurement
noise or a platform-specific artifact. An earlier measurement using a
smaller call count per trial (1,000 calls) produced unreliable, high-variance
results (up to 51% relative stdev) on the faster-running function, because
its shorter trial duration made it disproportionately sensitive to
fixed-cost system interruptions (garbage collection pauses, OS scheduler
jitter); increasing the call count to 20,000 resolved this by amortizing
fixed overhead over a longer, more comparable trial duration. Full
measurement code, including the environment-reporting and outlier-detection
logic, is provided in `benchmarks/benchmark_latency.py` for independent
reproduction.

# Limitations

The romanization scheme is a practical, ASCII-only transliteration and is
not reversible (Roman output cannot be deterministically mapped back to the
original Bangla input), unlike IAST/ISO 15919. The language-identification
and dialectal coverage of the toolkit is limited to script-level detection;
it does not distinguish between Bangla and Bengali-script text written in
related but distinct languages (e.g. Chakma, Garo, or Marma written in
Bengali script), which is a separate, unsolved problem noted as future work.

# Acknowledgements

TODO — acknowledge any advisors, labs, or funding sources if applicable.

# References