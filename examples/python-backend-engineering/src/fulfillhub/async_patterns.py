"""Deterministic lost updates and explicit gather/TaskGroup failure ownership."""

import asyncio
from typing import Literal


async def counter_experiment(*, workers: int = 20) -> tuple[int, int]:
    if workers < 1 or workers > 1000:
        raise ValueError("workers must be 1..1000")
    state = {"count": 0}
    barrier = asyncio.Barrier(workers)

    async def unsafe() -> None:
        before = state["count"]
        await barrier.wait()  # All readers see zero before any task writes.
        state["count"] = before + 1

    async with asyncio.TaskGroup() as group:
        for _ in range(workers):
            group.create_task(unsafe())
    lost = state["count"]
    state["count"] = 0
    lock = asyncio.Lock()

    async def safe() -> None:
        async with lock:
            before = state["count"]
            await asyncio.sleep(0)  # Keep the same suspension opportunity under the lock.
            state["count"] = before + 1

    async with asyncio.TaskGroup() as group:
        for _ in range(workers):
            group.create_task(safe())
    return lost, state["count"]


async def failure_experiment(mode: Literal["gather", "taskgroup"]) -> tuple[str, ...]:
    events: list[str] = []
    started = asyncio.Event()
    release = asyncio.Event()

    async def sibling() -> None:
        events.append("sibling started")
        started.set()
        try:
            await release.wait()
            events.append("sibling completed")
        except asyncio.CancelledError:
            events.append("sibling cancelled")
            raise
        finally:
            events.append("sibling cleaned")

    async def fail() -> None:
        await started.wait()
        raise RuntimeError("deliberate child failure")

    if mode == "gather":
        children = [asyncio.create_task(sibling()), asyncio.create_task(fail())]
        try:
            try:
                await asyncio.gather(*children)
            except RuntimeError:
                events.append("parent caught failure")
                release.set()
                await children[0]  # gather did not cancel the sibling; we still own it.
        finally:
            for child in children:
                if not child.done():
                    child.cancel()
            await asyncio.gather(*children, return_exceptions=True)
    elif mode == "taskgroup":
        try:
            async with asyncio.TaskGroup() as group:
                group.create_task(sibling())
                group.create_task(fail())
        except* RuntimeError:
            events.append("parent caught failure")
    else:
        raise ValueError("unknown mode")
    return tuple(events)


async def demo() -> None:
    print("unsafe and locked counts:", await counter_experiment())
    for mode in ("gather", "taskgroup"):
        print(mode, await failure_experiment(mode))


if __name__ == "__main__":
    asyncio.run(demo())
