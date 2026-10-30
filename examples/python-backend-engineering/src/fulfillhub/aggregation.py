"""Bounded HTTP fan-out with one shared pool and structured task ownership."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

import httpx


@dataclass(frozen=True, slots=True)
class Result:
    url: str
    status: int | None
    body: str | None
    error: str | None


async def aggregate(
    urls: Sequence[str],
    *,
    concurrency: int = 4,
    request_timeout: float = 0.5,
    queue_size: int = 8,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[Result]:
    if isinstance(concurrency, bool) or not isinstance(concurrency, int) or concurrency < 1:
        raise ValueError("concurrency must be a positive integer")
    if isinstance(queue_size, bool) or not isinstance(queue_size, int) or queue_size < 1:
        raise ValueError("queue_size must be a positive integer")
    if isinstance(request_timeout, bool) or not isinstance(request_timeout, (int, float)):
        raise ValueError("request_timeout must be a positive finite number")
    try:
        timeout_seconds = float(request_timeout)
    except OverflowError as exc:
        raise ValueError("request_timeout must be a positive finite number") from exc
    if not isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("request_timeout must be a positive finite number")
    queue: asyncio.Queue[tuple[int, str] | None] = asyncio.Queue(maxsize=queue_size)
    results: list[Result | None] = [None] * len(urls)
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)

    async def produce() -> None:
        for index, url in enumerate(urls):
            await queue.put((index, url))
        for _ in range(concurrency):
            await queue.put(None)

    async def consume(client: httpx.AsyncClient) -> None:
        while True:
            item = await queue.get()
            try:
                if item is None:
                    return
                index, url = item
                try:
                    # Queue waiting is excluded; this is a per-request deadline.
                    async with asyncio.timeout(timeout_seconds):
                        response = await client.get(url)
                        response.raise_for_status()
                    results[index] = Result(url, response.status_code, response.text, None)
                except TimeoutError, httpx.TimeoutException:
                    results[index] = Result(url, None, None, "timeout")
                except httpx.HTTPStatusError as exc:
                    results[index] = Result(url, exc.response.status_code, None, "http_status")
                except httpx.RequestError:
                    results[index] = Result(url, None, None, "request_error")
            finally:
                queue.task_done()

    # Do not use ambient proxy settings for this local learning client.
    # TLS verification remains enabled. Real deployments should choose proxy policy explicitly.
    async with httpx.AsyncClient(
        limits=limits, timeout=timeout_seconds, trust_env=False, transport=transport
    ) as client:
        async with asyncio.TaskGroup() as group:
            group.create_task(produce(), name="producer")
            for index in range(concurrency):
                group.create_task(consume(client), name=f"worker-{index}")

    # Returning partial output would hide a broken worker/protocol invariant.
    if any(result is None for result in results):
        raise RuntimeError("aggregation ended without a result for every URL")
    return [result for result in results if result is not None]
