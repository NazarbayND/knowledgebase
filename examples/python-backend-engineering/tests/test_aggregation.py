import asyncio

import httpx
import pytest

from fulfillhub.aggregation import aggregate
from fulfillhub.concurrency_lab import local_api


def test_bounded_concurrency_and_order() -> None:
    async def scenario() -> None:
        active = 0
        peak = 0
        first_wave = asyncio.Event()

        async def handle(request: httpx.Request) -> httpx.Response:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            try:
                if active == 3:
                    first_wave.set()
                # Synchronize the first wave; sleep(0) alone cannot guarantee overlap.
                await first_wave.wait()
                return httpx.Response(200, text=request.url.path)
            finally:
                active -= 1

        urls = [f"http://example.test/{index}" for index in range(20)]
        results = await aggregate(
            urls, concurrency=3, queue_size=1, transport=httpx.MockTransport(handle)
        )
        assert [result.body for result in results] == [f"/{index}" for index in range(20)]
        assert all(result.error is None for result in results)
        assert 1 < peak <= 3
        assert active == 0

    asyncio.run(scenario())


def test_timeout_status_and_transport_failure_are_distinct() -> None:
    async def scenario() -> None:
        async def handle(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/timeout":
                await asyncio.Event().wait()
            if request.url.path == "/offline":
                raise httpx.ConnectError("offline", request=request)
            return httpx.Response(503)

        results = await aggregate(
            [f"http://example.test/{name}" for name in ("timeout", "status", "offline")],
            request_timeout=0.02,
            transport=httpx.MockTransport(handle),
        )
        assert [(r.status, r.error) for r in results] == [
            (None, "timeout"),
            (503, "http_status"),
            (None, "request_error"),
        ]

    asyncio.run(scenario())


def test_parent_cancellation_cleans_up_all_workers() -> None:
    async def scenario() -> None:
        started = asyncio.Event()
        active = 0

        async def handle(request: httpx.Request) -> httpx.Response:
            nonlocal active
            active += 1
            started.set()
            try:
                await asyncio.Event().wait()
                return httpx.Response(200)
            finally:
                active -= 1

        task = asyncio.create_task(
            aggregate(
                ["http://example.test/slow"] * 20,
                concurrency=2,
                queue_size=1,
                transport=httpx.MockTransport(handle),
            )
        )
        await asyncio.wait_for(started.wait(), timeout=2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert active == 0
        assert not any(
            t.get_name() == "producer" or t.get_name().startswith("worker-")
            for t in asyncio.all_tasks()
            if not t.done()
        )

    asyncio.run(scenario())


def test_programming_failure_cancels_siblings() -> None:
    async def scenario() -> None:
        async def handle(request: httpx.Request) -> httpx.Response:
            raise RuntimeError("unexpected defect")

        with pytest.raises(ExceptionGroup) as caught:
            await aggregate(
                ["http://example.test/"] * 8,
                transport=httpx.MockTransport(handle),
            )
        assert any(isinstance(error, RuntimeError) for error in caught.value.exceptions)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "options",
    [
        {"concurrency": 0},
        {"concurrency": -1},
        {"concurrency": True},
        {"concurrency": 1.5},
        {"concurrency": "2"},
        {"queue_size": 0},
        {"queue_size": -1},
        {"queue_size": True},
        {"queue_size": 1.5},
        {"queue_size": "2"},
        {"request_timeout": 0},
        {"request_timeout": -1},
        {"request_timeout": True},
        {"request_timeout": "2"},
        {"request_timeout": None},
        {"request_timeout": float("nan")},
        {"request_timeout": float("inf")},
        {"request_timeout": float("-inf")},
        {"request_timeout": 10**1000},
    ],
)
def test_invalid_resource_limits(options: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        asyncio.run(aggregate([], **options))


def test_empty_batch() -> None:
    assert asyncio.run(aggregate([])) == []


def test_positive_integer_timeout_is_supported() -> None:
    assert asyncio.run(aggregate([], request_timeout=1)) == []


def test_real_http_boundary() -> None:
    with local_api() as base_url:
        results = asyncio.run(aggregate([f"{base_url}/ok", f"{base_url}/fail"]))
    assert results[0].status == 200
    assert results[0].body == '{"path": "/ok"}'
    assert results[1].status == 503
    assert results[1].error == "http_status"
