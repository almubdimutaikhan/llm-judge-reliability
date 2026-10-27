"""Set agreement, ranking agreement, and case-level uncertainty."""
import itertools
import math
import random
from statistics import mean


def jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        raise ValueError("Two missing sets are not perfect agreement")
    return len(a & b) / len(a | b)


def kendall(a, b):
    if set(a) != set(b) or len(a) != len(set(a)):
        raise ValueError("Rankings must be permutations of the same items")
    pos = {d: i for i, d in enumerate(b)}
    inv = sum(pos[x] > pos[y] for x, y in itertools.combinations(a, 2))
    return 1 - 2*inv / math.comb(len(a), 2)


def bootstrap_cases(values, repeats=10000):
    """values: one number per independent case; equal weight per case."""
    rng = random.Random(20261027)
    draws = sorted(mean(rng.choices(values, k=len(values))) for _ in range(repeats))
    return {"mean": mean(values), "ci_low": draws[int(.025*repeats)],
            "ci_high": draws[int(.975*repeats)], "cases": len(values)}
