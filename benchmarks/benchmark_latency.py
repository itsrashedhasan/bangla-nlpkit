"""
benchmark_latency.py

Controlled latency comparison between bangla-nlpkit and indic_transliteration.

Methodology:
  - Fixed input text (not varied across trials)
  - N independent trials, each timing M repeated calls
  - Warm-up trial discarded (avoids import/JIT/cache noise)
  - Reports mean, standard deviation, min, max across trials
  - Uses time.perf_counter() (monotonic, high-resolution, appropriate for
    benchmarking — NOT time.time())

This replaces the single-loop informal timing used during development,
which reported one number with no variance information and is not a
defensible measurement for a paper.
"""

import time
import statistics

from bangla_nlpkit.romanizer import romanize as bnk_romanize
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate as iso_transliterate

# Fixed test input — one realistic sentence, held constant across all trials
TEXT = "আমি বাংলায় কথা বলি এবং এটি আমার মাতৃভাষা"

N_TRIALS = 10           # independent trials
CALLS_PER_TRIAL = 20000 # calls timed within each trial — increased from 1000
                        # because at 1000 calls, bangla-nlpkit's much shorter
                        # per-trial duration made it disproportionately
                        # sensitive to fixed-cost noise (GC pauses, OS
                        # scheduler jitter), producing artificially high
                        # variance unrelated to the function's actual speed.
                        # A larger call count amortizes fixed-cost noise
                        # over a longer, more comparable trial duration.


def time_function(fn, *args, calls: int = CALLS_PER_TRIAL) -> float:
    """Time `calls` repeated invocations of fn(*args); return elapsed seconds."""
    start = time.perf_counter()
    for _ in range(calls):
        fn(*args)
    return time.perf_counter() - start


def run_controlled_benchmark():
    print("=" * 90)
    print("CONTROLLED LATENCY BENCHMARK")
    print(f"Input: {TEXT!r}")
    print(f"Trials: {N_TRIALS} (1 warm-up, discarded) | Calls per trial: {CALLS_PER_TRIAL}")
    print("=" * 90)

    # --- Warm-up (discarded) — avoids first-call import/cache overhead skewing results ---
    time_function(bnk_romanize, TEXT, calls=CALLS_PER_TRIAL)
    time_function(iso_transliterate, TEXT, sanscript.BENGALI, sanscript.ISO, calls=CALLS_PER_TRIAL)

    # --- bangla-nlpkit trials ---
    bnk_times = [time_function(bnk_romanize, TEXT) for _ in range(N_TRIALS)]

    # --- indic_transliteration trials ---
    iso_times = [
        time_function(iso_transliterate, TEXT, sanscript.BENGALI, sanscript.ISO)
        for _ in range(N_TRIALS)
    ]

    def report(name, times):
        mean = statistics.mean(times)
        median = statistics.median(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0.0
        relative_stdev = (stdev / mean * 100) if mean > 0 else 0.0
        per_call_mean_us = (mean / CALLS_PER_TRIAL) * 1_000_000
        per_call_median_us = (median / CALLS_PER_TRIAL) * 1_000_000
        print(f"\n{name}")
        print(f"  Trials (sec, {CALLS_PER_TRIAL} calls each): {[f'{t:.4f}' for t in times]}")
        print(f"  Mean:   {mean:.4f} sec  (± {stdev:.4f} sec, {relative_stdev:.1f}% relative stdev, {N_TRIALS} trials)")
        print(f"  Median: {median:.4f} sec  (more robust to single-trial outliers/OS jitter)")
        print(f"  Min/Max: {min(times):.4f} / {max(times):.4f} sec")
        print(f"  Per-call latency (mean):   {per_call_mean_us:.2f} microseconds")
        print(f"  Per-call latency (median): {per_call_median_us:.2f} microseconds")
        if relative_stdev > 15:
            print(f"  ⚠ WARNING: relative stdev > 15% — results may be affected by system")
            print(f"    noise (background processes, thermal throttling, OS scheduling).")
            print(f"    Consider closing background applications and re-running, or report")
            print(f"    median rather than mean as the primary statistic.")
        return mean, median, stdev

    bnk_mean, bnk_median, bnk_stdev = report("bangla-nlpkit", bnk_times)
    iso_mean, iso_median, iso_stdev = report("indic_transliteration (ISO 15919)", iso_times)

    print(f"\n{'='*90}")
    print("SUMMARY FOR paper.md")
    print(f"{'='*90}")
    ratio_mean = iso_mean / bnk_mean
    ratio_median = iso_median / bnk_median
    print(f"bangla-nlpkit:          mean {bnk_mean/CALLS_PER_TRIAL*1e6:.2f} µs/call | median {bnk_median/CALLS_PER_TRIAL*1e6:.2f} µs/call")
    print(f"indic_transliteration:  mean {iso_mean/CALLS_PER_TRIAL*1e6:.2f} µs/call | median {iso_median/CALLS_PER_TRIAL*1e6:.2f} µs/call")
    print(f"Ratio (mean):   indic_transliteration is {ratio_mean:.2f}x slower per call")
    print(f"Ratio (median): indic_transliteration is {ratio_median:.2f}x slower per call")
    print()
    print("Report the MEDIAN ratio as primary if mean and median disagree substantially —")
    print("median is robust to single-trial outliers caused by OS/system noise, which mean is not.")
    print()
    print("NOTE: Results are environment-dependent (CPU, Python version, system load).")
    print("Report your specific environment (CPU model, Python version, OS) alongside")
    print("these numbers in the paper for reproducibility.")

    import platform
    print()
    print("Environment:")
    print(f"  Python: {platform.python_version()}")
    print(f"  Platform: {platform.platform()}")
    print(f"  Processor: {platform.processor()}")


if __name__ == "__main__":
    run_controlled_benchmark()