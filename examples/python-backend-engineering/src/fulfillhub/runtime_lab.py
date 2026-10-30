"""Inspect bytecode, runtime identity, allocation peaks and CPU profiles."""

import cProfile
import dis
import gc
import platform
import sys
import tracemalloc
from collections.abc import Iterator
from itertools import islice


def squares(limit: int) -> Iterator[int]:
    return (value * value for value in range(limit))


def workload(limit: int) -> int:
    return sum(squares(limit))


def main() -> None:
    print(
        "implementation:", platform.python_implementation(), "version:", platform.python_version()
    )
    gil_status = getattr(sys, "_is_gil_enabled", None)
    print("GIL enabled:", gil_status() if gil_status is not None else "probe unavailable")
    print("first squares:", list(islice(squares(100), 4)))
    print("GC enabled:", gc.isenabled())
    dis.dis(workload)
    tracemalloc.start()
    result = workload(100_000)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print("sum:", result, "traced current bytes:", current, "traced peak bytes:", peak)
    cProfile.runctx("workload(100_000)", globals(), locals(), sort="cumtime")


if __name__ == "__main__":
    main()
