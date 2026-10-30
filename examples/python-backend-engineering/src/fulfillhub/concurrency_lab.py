"""Controlled experiments; wall-clock numbers are observations, not test assertions."""

import argparse
import asyncio
import json
import threading
import time
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fulfillhub.aggregation import aggregate


@contextmanager
def local_api() -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            status = 503 if self.path == "/fail" else 200
            time.sleep(0.2 if self.path == "/slow" else 0.02)
            body = json.dumps({"path": self.path}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except BrokenPipeError, ConnectionResetError:
                pass  # A timed-out client may have closed its socket.

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


async def scheduling_probe(mode: str, *, tasks: int = 4, delay: float = 0.03) -> int:
    """Count heartbeat turns while sleepers run, including one deliberate blocking mode."""
    stop = asyncio.Event()
    turns = 0

    async def heartbeat() -> None:
        nonlocal turns
        while not stop.is_set():
            turns += 1
            await asyncio.sleep(0.002)

    async def work() -> None:
        if mode == "blocking":
            # Deliberate blocking defect for comparison with the two corrected modes.
            time.sleep(delay)  # noqa: ASYNC251
        elif mode == "thread":
            await asyncio.to_thread(time.sleep, delay)
        elif mode == "cooperative":
            await asyncio.sleep(delay)
        else:
            raise ValueError("unknown mode")

    pulse = asyncio.create_task(heartbeat())
    try:
        async with asyncio.TaskGroup() as group:
            for _ in range(tasks):
                group.create_task(work())
    finally:
        stop.set()
        await pulse
    return turns


def cpu_work(limit: int) -> int:
    return sum(number * number for number in range(limit))


def executor_probe() -> None:
    values = [150_000] * 4
    expected = [cpu_work(value) for value in values]
    for executor_type in (ThreadPoolExecutor, ProcessPoolExecutor):
        started = time.perf_counter()
        with executor_type(max_workers=2) as pool:
            results = list(pool.map(cpu_work, values))
        if results != expected:
            raise RuntimeError("executor produced incorrect results")
        print(executor_type.__name__, "seconds=", round(time.perf_counter() - started, 4))


async def demo(base_url: str) -> None:
    urls = [f"{base_url}/ok/{index}" for index in range(8)]
    for workers in (1, 4):
        started = time.perf_counter()
        results = await aggregate(urls, concurrency=workers, request_timeout=1)
        elapsed = time.perf_counter() - started
        failures = sum(result.error is not None for result in results)
        print(f"workers={workers} results={len(results)} failures={failures} seconds={elapsed:.4f}")
    results = await aggregate([f"{base_url}/slow", f"{base_url}/fail"], request_timeout=0.05)
    print("deliberate failures:", [(result.status, result.error) for result in results])
    for mode in ("blocking", "cooperative", "thread"):
        print(mode, "heartbeat_turns=", await scheduling_probe(mode))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executors", action="store_true")
    args = parser.parse_args()
    if args.executors:
        executor_probe()
    else:
        with local_api() as base_url:
            asyncio.run(demo(base_url))


if __name__ == "__main__":
    main()
