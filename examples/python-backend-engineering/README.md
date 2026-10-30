# Python Backend Engineering examples

Python **3.14** is the course baseline. These examples are a learning package,
not the production FulfillHub service. The documentation site uses its own
Python 3.12 environment.

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed.
From this directory (`examples/python-backend-engineering/`):

```bash
uv python install 3.14
uv sync --frozen
```

`uv.lock` records direct, transitive, and development dependencies. The build backend
is declared separately in `pyproject.toml`. Do not
regenerate it merely to install. To update dependencies deliberately, run
`uv lock --upgrade`, then run all checks below and review the lockfile diff.

## Run and check

```bash
uv run --frozen python -m fulfillhub
uv run --frozen python -m fulfillhub.runtime_lab
uv run --frozen python -m fulfillhub.concurrency_lab
uv run --frozen python -m fulfillhub.concurrency_lab --executors
uv run --frozen pytest
uv run --frozen mypy
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv build --wheel
```

The inventory demo prints stock changing from 3 to 1 while the original product
remains unchanged. The runtime lab prints the interpreter, GIL status, bytecode,
allocation statistics, and CPU profile. Bytecode and measured values vary by runtime.

The concurrency lab starts a temporary loopback HTTP server on an assigned port,
aggregates eight requests using one and four workers, demonstrates a timeout and
HTTP 503, and compares heartbeat progress with blocking/cooperative/threaded work.
It shuts its server down before exiting. Timing is observational; tests assert
behavior and concurrency bounds instead of speed ratios. The executor variant
checks equal CPU results from thread/process pools; process startup can dominate
this small workload. No database, external API, credentials, or Docker is needed.

## Boundaries

- The inventory service is single-process and not transaction-safe. Tenant keys
  prevent accidental lookup collisions, not unauthorized access. Authentication
  and transactional concurrency arrive in later course phases.
- The JSON repository uses atomic file replacement for a single writer. It has
  no multi-writer locking, crash-durability guarantee, or schema migration system.
- The HTTP aggregator handles a finite, trusted URL list. Pending work is bounded,
  but results and response bodies are retained in memory. URL allowlisting, body
  limits, total-batch deadlines, retries, rate limiting, and production proxy
  policy are exercise/design topics, not claimed features.
- Cancelling an async wait on a thread does not terminate the running thread.

Generated virtual environments and caches are ignored. The labs create no
persistent files; tests use pytest-managed temporary directories. A manual JSON
repository experiment writes to the path you supply; remove that file when done.
The wheel build writes to the ignored `dist/` directory. CI uses uv 0.12.23.

Lessons and acceptance criteria live under
`docs/python-backend-engineering/phase-1/` and `phase-2/` in the repository.
