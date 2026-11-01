"""
LANDSCAPE: what the "terrain" of the objective function f(s) looks like over the state space.

We do two things:
  1. The size of the space (how many states exist), written as 10^x.
  2. Sampling: we take many random complete states and look at the
     distribution of f(s). Solutions (f = 0) usually never show up,
     because they are "a needle in a haystack". This shows why we need a systematic
     search with backtracking rather than random guessing.
"""

import random
from collections import Counter


def sample_objective(problem, samples=2000, seed=42):
    rng = random.Random(seed)
    values = [problem.objective(problem.random_state(rng)) for _ in range(samples)]
    hist = sorted(Counter(values).items())
    return {
        "samples": samples,
        "min": min(values),
        "max": max(values),
        "mean": round(sum(values) / samples, 2),
        "zeros": values.count(0),
        "histogram": hist,
    }


def print_histogram(result, width=50):
    hist = result["histogram"]
    top = max(c for _, c in hist)
    print(f"  {result['samples']} gjendje te rastesishme | f min={result['min']}  "
          f"mesatarja={result['mean']}  max={result['max']} | zgjidhje te gjetura: {result['zeros']}")
    # group into about 15 bars so it is easy to read
    lo, hi = result["min"], result["max"]
    step = max(1, (hi - lo + 1) // 15)
    buckets = Counter()
    for f, c in hist:
        buckets[lo + ((f - lo) // step) * step] += c
    top = max(buckets.values())
    for b in sorted(buckets):
        label = f"{b}" if step == 1 else f"{b}-{b + step - 1}"
        bar = "#" * max(1, round(buckets[b] / top * width))
        print(f"  f={label:>9} | {bar} {buckets[b]}")


def print_sizes(rows):
    for text, log10 in rows:
        if log10 is None:
            print(f"  {text:45} : e panjohur")
        else:
            print(f"  {text:45} : ~10^{log10:.1f}")
