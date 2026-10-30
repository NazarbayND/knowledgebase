"""Compare equivalent membership workloads; timings are observations."""

import statistics
import timeit
import tracemalloc
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass


def count_matches(allowed: Collection[int], queries: Sequence[int]) -> int:
    return sum(value in allowed for value in queries)


def indexed_count(values: Sequence[int], queries: Sequence[int]) -> int:
    # Index construction is intentionally included in the candidate's measured work.
    return count_matches(set(values), queries)


def allocation_peak(function: Callable[[], int]) -> int:
    tracemalloc.start()
    try:
        function()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


@dataclass(frozen=True)
class Measurement:
    size: int
    matches: int
    scan_seconds: float
    index_seconds: float
    scan_peak_bytes: int
    index_peak_bytes: int


def measure(size: int, *, repeats: int = 3) -> Measurement:
    if size < 1 or size > 10_000 or repeats < 1 or repeats > 20:
        raise ValueError("size must be 1..10000 and repeats 1..20")
    values = list(range(size))
    queries = list(range(0, size * 2, 2))

    def scan() -> int:
        return count_matches(values, queries)

    def indexed() -> int:
        return indexed_count(values, queries)

    expected = scan()  # Also warms both paths before measurement.
    if indexed() != expected:
        raise RuntimeError("candidate changed the result")
    return Measurement(
        size=size,
        matches=expected,
        scan_seconds=statistics.median(timeit.repeat(scan, number=1, repeat=repeats)),
        index_seconds=statistics.median(timeit.repeat(indexed, number=1, repeat=repeats)),
        scan_peak_bytes=allocation_peak(scan),
        index_peak_bytes=allocation_peak(indexed),
    )


def main() -> None:
    for size in (100, 1000, 5000):
        print(measure(size))


if __name__ == "__main__":
    main()
