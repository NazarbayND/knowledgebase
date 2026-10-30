import asyncio

import pytest

from fulfillhub.async_patterns import counter_experiment, failure_experiment


@pytest.mark.parametrize("workers", [1, 2, 20])
def test_barrier_reproduces_lost_update_and_lock_preserves_all_updates(workers: int) -> None:
    assert asyncio.run(counter_experiment(workers=workers)) == (1, workers)


@pytest.mark.parametrize("workers", [0, -1, 1001])
def test_invalid_worker_count(workers: int) -> None:
    with pytest.raises(ValueError):
        asyncio.run(counter_experiment(workers=workers))


def test_gather_keeps_sibling_alive_until_owner_releases_it() -> None:
    assert asyncio.run(failure_experiment("gather")) == (
        "sibling started",
        "parent caught failure",
        "sibling completed",
        "sibling cleaned",
    )


def test_taskgroup_cancels_and_cleans_sibling_before_parent_catches_failure() -> None:
    assert asyncio.run(failure_experiment("taskgroup")) == (
        "sibling started",
        "sibling cancelled",
        "sibling cleaned",
        "parent caught failure",
    )
