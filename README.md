# Engineering Knowledge Library

A topic-agnostic personal knowledge base built with MkDocs Material. Independent
subjects share a searchable library without sharing a prescribed curriculum
structure. Python Backend Engineering is the first subject, with Phases 1–2,
four modules, implementation exercises, interviews, assessments and practical projects.

Start at the [library dashboard](docs/index.md), explore the
[Python subject](docs/python-backend-engineering/index.md), or read the saved
[complete 16-week course plan](docs/python-backend-engineering/course-plan.md).

## Develop locally

Use Python 3.12 and run these commands from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m mkdocs serve --dev-addr 127.0.0.1:8000
```

On Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.

Validate the documentation before submitting changes:

```bash
.venv/bin/python -m pip check
.venv/bin/python -m mkdocs build --strict
```

The build checks navigation, internal page links, and heading anchors, and writes
the generated site to the ignored `site/` directory. External URL availability
is not checked. No application service, database, or secret is needed.

## Repository layout

```text
docs/
  index.md                       # General library dashboard
  library-guide.md               # Reading and authoring conventions
  python-backend-engineering/    # Independent subject
    index.md                     # Subject overview and chapter navigation
    learning-path.md             # Study sequence and prerequisites
    progress.md                  # Evidence and checkpoint log
    course-plan.md               # Complete supplied curriculum, including future phases
    phase-1/                     # Modules 1–2, practice, inventory project
    phase-2/                     # Modules 3–4, practice, runtime/concurrency project
examples/
  python-backend-engineering/    # Python 3.14 package, tests and uv.lock
mkdocs.yml                       # Platform and explicit navigation
requirements.in                  # Direct build dependencies
requirements.txt                 # Resolved build dependency versions
```

Runnable examples belong in `examples/<subject>/` when introduced with their
lessons. Do not create empty subject or example directories. Keep requirements
and execution instructions with each example so unrelated subjects can use
different tools without affecting the documentation build.

The implemented examples have a separate [setup and command guide](examples/python-backend-engineering/README.md).
Use Python 3.14 for them; changing their dependencies does not alter the site's
Python 3.12 build environment. The examples include memory/JSON inventory adapters,
runtime inspection/profiling, a bounded HTTP client and a temporary local HTTP lab.
The enriched study route also includes four worked walkthroughs, a streaming CSV
reporter, descriptor/decorator investigations, a membership benchmark, deterministic
race/failure labs, and cumulative assessments with model answers for both phases.

## Add or extend a subject

1. Create `docs/<subject>/index.md` and substantive learning material.
2. Give the subject its own learning path and progress/checkpoint page.
3. Add a sibling section under `nav` in `mkdocs.yml`, with the subject's index
   first. Add its pages beneath that section in the desired reading order.
4. Add one entry to the subject catalogue in `docs/index.md`.
5. Build with `--strict` and inspect the new navigation.

A course may use phases/modules/chapters. An article collection may instead use
articles/references/notes. These are choices within a subject, not global rules.
See the [library guide](docs/library-guide.md) for page and link conventions.

## Dependencies

`requirements.txt` pins the resolved Python 3.12 build environment. To update it,
change `requirements.in`, install those dependencies in a fresh Python 3.12
virtual environment, run `python -m pip freeze` into `requirements.txt`, then
run the strict build and a local preview before committing both files.

## GitHub Pages

The documentation workflow validates pull requests and pushes to `main`. To enable
automatic publication:

1. In repository Settings → Pages, select **GitHub Actions** as the source.
2. Push or merge changes into `main`.

After the documentation build and Python example checks succeed, pushes to `main`
automatically deploy the site. Pull requests run validation only. You can also
manually run the **Documentation** workflow on `main` to redeploy.

If the repository owner or name changes,
update `site_url`, `repo_url`, and `repo_name` in `mkdocs.yml`.
