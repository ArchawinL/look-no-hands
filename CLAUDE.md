# CLAUDE.md — agent operating rules for gazehint

Read `docs/PLAN.md` (architecture, layout, protocol) and `docs/MILESTONES.md` (stories) before doing anything.

## What this project is
A Homerow-style hint overlay (Rust) plus a webcam gaze and wink sidecar (Python first, C++ port later). The two talk over localhost TCP using newline-delimited JSON (protocol v1, defined in `protocol/`).

## Ownership: the most important rule
- `gaze-py/`, `protocol/`, CI, and docs are **agent-owned**. Implement them following the milestones.
- `core-rs/` and `gaze-cpp/` are **human-owned**. The human is using them to learn Rust and C++.
  - During M0, create only the skeletons described in PLAN.md §8.
  - After M0, **do not write or rewrite code there** unless the human explicitly says so for a specific story.
  - Do review, explain compiler errors, point to docs, and give hints. Prefer questions and pointers over finished code.
  - Never port Python logic into Rust or C++ unprompted, including the label generator and the filters.

## How to work
1. Pick the next unchecked **agent** story in `docs/MILESTONES.md` (or the one the human names). One story per branch: `p5-calibration`.
2. Restate the story's acceptance criteria before starting. If a criterion is unclear or impossible, ask.
3. Implement, then run the checks below.
4. **(manual)** criteria need a human with a webcam. List exactly what the human should do and what they should see, then wait. Never tick manual criteria yourself.
5. When done: tick the status board, add a Progress log row, and commit with the story ID as prefix (`P5: fit ridge calibration`).

## Commands
```
just py-sync         # uv sync in gaze-py
just py-test         # pytest -m "not hardware"
just py-lint         # ruff check, ruff format --check, mypy --strict src
just rs-check        # fmt --check, clippy -D warnings, build
just rs-test
just cpp-configure && just cpp-build && just cpp-test
just check-all       # everything; must be green before committing
```
Python code runs through `uv run` from `gaze-py/`, e.g. `uv run python -m gazehint_gaze doctor`.

## Python conventions
- Python version per decision D4; type hints everywhere; `mypy --strict` clean on `src/`.
- Keep pure logic (features, filters, calibration, winks, protocol) free of OpenCV/MediaPipe imports so it can be unit-tested without hardware.
- Tests that need a camera, model file, or display get `@pytest.mark.hardware`.
- Keep dependencies minimal; justify any new one in the commit message. Calibration uses numpy only.
- Monotonic time (`time.monotonic_ns`) for all timestamps; message `t_ms` is milliseconds since sidecar start.
- Live and replay must go through the same `pipeline.py` code path.

## Protocol rules
- `protocol/gaze.schema.json` is the contract. Any emitted message must validate against it.
- Adding optional fields keeps `v:1`. Renaming, removing, or changing meaning requires `v:2`, a note in `docs/protocol.md`, and the human's approval.
- `left`/`right` always mean the **user's** eyes (verified in P2).
- Coordinates are logical points on the primary display.

## Privacy and safety
- Never commit anything from `recordings/`, and never commit model files (`*.task`, `*.onnx`, `*.tflite`).
- Test fixtures must be synthetic unless the human explicitly approves real data.
- The TCP server binds to `127.0.0.1` only.
- Don't add telemetry or network calls, apart from the model download script.

## When unsure
Ask one clear question rather than guessing, especially about the open decisions D1–D6 in PLAN.md §4, anything touching human-owned code, and protocol changes.
