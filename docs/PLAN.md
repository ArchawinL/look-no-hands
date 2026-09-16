# look-no-hands — Repository Initialisation Plan

> Project name: **look-no-hands** (Python package `look_no_hands`, Rust crates `look-no-hands-*`).
> This file covers *how the repo is set up*. What to build and in what order lives in [`MILESTONES.md`](./MILESTONES.md).

## 1. What we're building

A hands-free / mouseless input tool:

1. **Hint mode (keyboard):** press a hotkey → every clickable element on screen gets a short home-row label (Homerow/Vimium style) → type the label → element is activated.
2. **Gaze mode (webcam):** gaze picks a *region* rather than a pixel → only elements in that region get labels (shorter labels), or the nearest candidate is highlighted → confirm with keys, **wink** (left = click, right = right-click), or dwell, depending on settings.

Design assumption: laptop-webcam gaze error is roughly 90–260 px. The system never trusts gaze for pixel precision; it uses gaze to *narrow* the candidate set.

## 2. Architecture

Two processes that talk over a local socket:

```
┌──────────────────────────── gaze sidecar ───────────────────────────┐
│ camera → face landmarks → features → calibration → smoothing        │
│                                   └→ wink detector                   │
│ → newline-delimited JSON over TCP 127.0.0.1:47800                    │
└─────────────────────────────────────────────────────────────────────┘
        gaze-py/  (reference implementation, built first, agent-owned)
        gaze-cpp/ (later port, human-owned, learning C++)
                                   │
                                   ▼
┌──────────────────────────── core app (Rust) ────────────────────────┐
│ ElementProvider(per OS) → RegionFilter → HintLabeler → Overlay      │
│ → Selector(keyboard | wink | dwell) → Activate                       │
└─────────────────────────────────────────────────────────────────────┘
        core-rs/  (skeleton now, human-owned, learning Rust)
```

The **protocol** (`protocol/`) is the contract between them. Both gaze implementations must produce messages that validate against the same schema and pass the same fixture tests.

## 3. Ownership model

| Area | Language | Owner | Agent may… |
|---|---|---|---|
| `gaze-py/` | Python | **Agent** (Claude Code) | Implement fully, following MILESTONES.md |
| `protocol/` | JSON Schema + fixtures | Agent, reviewed by human | Implement; changes need a version bump |
| `core-rs/` | Rust | **Human** (learning) | Create skeleton only; afterwards review, explain, hint — do not implement unless explicitly asked |
| `gaze-cpp/` | C++ | **Human** (learning) | Create skeleton only; same rules as Rust |
| CI, tooling, docs | — | Agent | Maintain |

## 4. Open decisions (settle before or during M0)

| # | Decision | Default if not decided |
|---|---|---|
| D1 | Primary development OS (decides first Rust platform backend) | Leave all three backends stubbed |
| D2 | Project name | `look-no-hands` |
| D3 | License | MIT |
| D4 | Python version pin | 3.12 — **verify** a `mediapipe` wheel exists for the pinned version and OS before committing |
| D5 | IPC transport and port | TCP `127.0.0.1:47800`, newline-delimited JSON |
| D6 | Coordinate space | Logical points (not physical pixels), primary display only, origin top-left. Multi-monitor is out of scope for v1. |

Record each settled decision as a short file in `docs/decisions/NNNN-title.md` (context / decision / consequences, ≤ 20 lines).

## 5. Target repository layout

```
look-no-hands/
├── CLAUDE.md                     # agent operating rules (read first)
├── README.md                     # quick start for humans
├── LICENSE
├── justfile                      # common commands across all three parts
├── .gitignore
├── .editorconfig
├── .github/workflows/ci.yml
├── docs/
│   ├── PLAN.md                   # this file
│   ├── MILESTONES.md             # stories + acceptance criteria + progress log
│   ├── protocol.md               # human-readable protocol spec
│   └── decisions/
│       └── 0001-language-split.md
├── protocol/
│   ├── gaze.schema.json          # JSON Schema (draft 2020-12), protocol v1
│   ├── targets.schema.json       # fake target list format (used by Python demo + Rust fake provider)
│   └── fixtures/
│       ├── gaze_stream_basic.jsonl
│       ├── wink_events.jsonl
│       └── targets_sample.json
├── gaze-py/
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/look_no_hands/
│   │   ├── __init__.py
│   │   ├── __main__.py           # CLI entry: `python -m look_no_hands <cmd>`
│   │   ├── cli.py
│   │   ├── config.py             # settings dataclasses, load/save (platformdirs)
│   │   ├── camera.py             # OpenCV capture, timestamps, FPS
│   │   ├── landmarks.py          # MediaPipe FaceLandmarker wrapper
│   │   ├── features.py           # iris offsets, eye openness, head pose
│   │   ├── calibration.py        # ridge regression mapping features → screen
│   │   ├── filters.py            # One Euro filter
│   │   ├── winks.py              # unilateral wink state machine
│   │   ├── ringbuffer.py         # time-indexed history (pre-wink gaze lookup)
│   │   ├── protocol.py           # message dataclasses + JSON (de)serialisation
│   │   ├── transport.py          # TCP server, multiple clients, backpressure
│   │   ├── pipeline.py           # wires everything; same code path live and replay
│   │   ├── recording.py          # record / replay sessions
│   │   ├── screen.py             # screen size in points, DPI helpers
│   │   └── tools/
│   │       ├── viewer.py         # debug window: landmarks, blendshapes, FPS
│   │       ├── calibrate.py      # fullscreen 9-point calibration
│   │       ├── validate.py       # accuracy board → error report
│   │       ├── wink_setup.py     # per-user wink thresholds
│   │       ├── listen.py         # tiny client that prints the stream
│   │       └── snap_demo.py      # end-to-end concept demo with fake targets
│   ├── scripts/download_models.py
│   ├── models/                   # .gitignored; face_landmarker.task goes here
│   └── tests/
│       ├── conftest.py
│       ├── test_filters.py
│       ├── test_calibration.py
│       ├── test_winks.py
│       ├── test_protocol.py
│       ├── test_ringbuffer.py
│       └── test_replay.py        # uses a tiny committed landmark-only fixture (no video)
├── core-rs/
│   ├── Cargo.toml                # workspace
│   ├── rust-toolchain.toml
│   └── crates/
│       ├── look-no-hands-core/        # pure logic, no OS calls
│       ├── look-no-hands-platform/    # per-OS element providers, overlay, input
│       └── look-no-hands-app/         # binary tying it together
├── gaze-cpp/
│   ├── CMakeLists.txt
│   ├── CMakePresets.json
│   ├── vcpkg.json
│   ├── include/look_no_hands/
│   ├── src/
│   └── tests/
└── recordings/                   # .gitignored — contains face video, never commit
```

## 6. Tooling

**Python (`gaze-py/`)**
- Environment and dependencies: `uv` (`uv sync`, `uv run`).
- Runtime dependencies: `mediapipe`, `opencv-python`, `numpy`, `platformdirs`, `screeninfo`. Keep the list short; justify any addition in the PR/commit message.
- Dev dependencies: `pytest`, `ruff` (lint + format), `mypy` (strict on `src/`), `jsonschema` (tests only).
- Pytest markers: `hardware` (needs camera/model/display; skipped in CI by default), `slow`.
- Calibration maths uses plain numpy (closed-form ridge regression); no scikit-learn.

**Rust (`core-rs/`)**
- Stable toolchain pinned in `rust-toolchain.toml`, with `rustfmt` and `clippy` components.
- Skeleton has **zero external crates**. The human adds crates as part of learning milestones.

**C++ (`gaze-cpp/`)**
- C++20, CMake ≥ 3.24, presets for `debug`, `debug-asan`, `release`.
- `vcpkg.json` manifest starts with an **empty** dependency list so the skeleton builds with no packages installed. Dependencies (OpenCV, ONNX Runtime, Eigen, Catch2, nlohmann-json) are added in the C++ milestones.
- Tests run through CTest; the skeleton uses a plain `main()`-based test executable until Catch2 is added.

**Repo-wide**
- `justfile` recipes: `py-sync`, `py-test`, `py-lint`, `rs-check`, `rs-test`, `cpp-configure`, `cpp-build`, `cpp-test`, `check-all`.
- CI (GitHub Actions):
  - `python`: ubuntu-latest, `uv sync`, ruff, mypy, `pytest -m "not hardware"`.
  - `rust`: matrix ubuntu/macos/windows, `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo build`, `cargo test`.
  - `cpp`: ubuntu-latest, configure/build/test with the `debug` preset.
  - `protocol`: validates all fixtures against the schemas (runs inside the python job).

`.gitignore` must include: `gaze-py/models/`, `recordings/`, `*.task`, `*.onnx`, `*.tflite`, `target/`, `build/`, `.venv/`, `__pycache__/`, `.DS_Store`, `vcpkg_installed/`.

## 7. Protocol v1 (summary — full spec goes in `docs/protocol.md`)

Transport: TCP `127.0.0.1:47800`. The sidecar is the server; any number of clients may connect. One JSON object per line, UTF-8. Clients must ignore unknown fields and unknown `type` values.

Every message has `"v": 1`, a `"type"`, and `"t_ms"` (monotonic milliseconds since sidecar start).

```jsonc
// type: gaze — emitted every processed frame while a face is tracked
{"v":1,"type":"gaze","t_ms":12345,"x":812.4,"y":440.1,"conf":0.82,
 "raw_x":798.0,"raw_y":452.7,                  // pre-smoothing, for debugging
 "head":{"yaw":-3.1,"pitch":5.2,"roll":0.4},    // degrees
 "eyes":{"blink_l":0.08,"blink_r":0.11}}        // blendshape scores 0..1, SUBJECT's left/right

// type: wink — emitted once per accepted wink
{"v":1,"type":"wink","t_ms":12890,"eye":"left",
 "x":805.0,"y":438.9,                           // gaze locked from BEFORE wink onset
 "lock_t_ms":12640,"duration_ms":230}

// type: status — on change, and every 1 s as a heartbeat
{"v":1,"type":"status","t_ms":13000,
 "state":"tracking",                            // tracking | no_face | uncalibrated | calibrating | paused
 "fps":29.7,"profile":"default"}
```

Conventions:
- `eye: "left"` always means the **user's** left eye, regardless of camera mirroring. This must be verified by a manual test (see P2).
- `x`/`y` are logical points on the primary display (D6). They may lie slightly off-screen; clients clamp.
- Version bump rule: adding optional fields keeps `v:1`; renaming, removing, or changing meaning requires `v:2`.

`targets.schema.json` (for the Python snap demo and the future Rust fake provider):

```json
{"screen":{"w":1512,"h":982},
 "targets":[{"id":"t1","x":20,"y":10,"w":28,"h":24,"role":"button","name":"Back"}]}
```

## 8. Skeleton specifications (M0 only — do not implement beyond this)

### 8.1 Rust skeleton (`core-rs/`)

Must pass `cargo build`, `cargo test`, `cargo clippy -- -D warnings`, and `cargo fmt --check` on all three OSes.

`look-no-hands-core/src/lib.rs` exposes these modules, each with doc comments and `todo!()` bodies:

```rust
// geometry.rs
pub struct Point { pub x: f64, pub y: f64 }
pub struct Rect { pub x: f64, pub y: f64, pub w: f64, pub h: f64 }
impl Rect {
    pub fn center(&self) -> Point { todo!("R1") }
    pub fn intersects(&self, other: &Rect) -> bool { todo!("R1") }
}

// target.rs
pub enum Role { Button, Link, MenuItem, Tab, CheckBox, TextField, Other }
pub struct Target { pub id: String, pub rect: Rect, pub role: Role, pub name: Option<String> }

// provider.rs
pub trait ElementProvider {
    fn targets(&mut self) -> Result<Vec<Target>, ProviderError>;
}
pub enum ProviderError { PermissionDenied, Unsupported, Other(String) }

// region.rs
pub enum Region { FullScreen, Circle { center: Point, radius: f64 } }
pub fn filter_targets(targets: &[Target], region: &Region) -> Vec<Target> { todo!("R2") }

// hints.rs
pub fn generate_labels(count: usize, alphabet: &str) -> Vec<String> { todo!("R1") }

// selector.rs
pub enum Selection { Pending, Chosen { target_id: String, action: Action }, Cancelled }
pub enum Action { Primary, Secondary }
pub trait Selector {
    fn on_key(&mut self, key: char) -> Selection;
}

// gaze.rs — mirrors protocol v1; parsing comes later (R7)
pub enum GazeMessage { Gaze { t_ms: u64, x: f64, y: f64, conf: f64 }, Wink { eye: Eye, x: f64, y: f64 }, Status { state: String } }
pub enum Eye { Left, Right }
```

Tests: one test per `todo!()` function, marked `#[ignore = "R1: implement generate_labels"]`, etc., containing the real assertions so un-ignoring them is the human's first task. Example for `generate_labels`: 30 labels from `"asdfjkl;"` are unique, and no label is a prefix of another.

`look-no-hands-platform/src/lib.rs`: `#[cfg(target_os = "macos")] mod macos;`, `windows`, `linux`, each exposing a `NativeProvider` struct implementing `ElementProvider` that returns `Err(ProviderError::Unsupported)`. Also empty `overlay.rs` and `input.rs` files with module docs describing their future job.

`look-no-hands-app/src/main.rs`: prints the version plus "hint mode not implemented yet — see docs/MILESTONES.md (R-track)" and exits 0.

Each crate gets a `README.md` of ≤ 15 lines stating its responsibility and which milestones touch it.

### 8.2 C++ skeleton (`gaze-cpp/`)

Must configure, build, and pass `ctest` on ubuntu with no vcpkg packages installed.

- Targets: `look_no_hands_gaze` (static library), `look-no-hands-gaze` (executable), `look_no_hands_tests` (test executable).
- `CMakeLists.txt` sets `CMAKE_CXX_STANDARD 20`, turns on warnings (`-Wall -Wextra -Wpedantic` / `/W4`), and adds an option `LOOK_NO_HANDS_SANITIZE` that enables ASan+UBSan on non-MSVC compilers.
- Headers in `include/look_no_hands/`, each with the interface declared and a comment block pointing to its milestone:
  - `one_euro.hpp` — `class OneEuroFilter { double filter(double value, double t_seconds); void reset(); }`
  - `calibration.hpp` — `struct FeatureVector`, `class Calibration { void fit(...); std::pair<double,double> predict(const FeatureVector&) const; bool load(path); bool save(path) const; }`
  - `wink_detector.hpp` — `enum class Eye`, `struct WinkEvent`, `class WinkDetector { std::optional<WinkEvent> update(double blink_l, double blink_r, int64_t t_ms); }`
  - `protocol.hpp` — structs mirroring protocol v1 plus `std::string to_json_line(...)` declarations
  - `landmarks.hpp` — `class LandmarkModel` interface (pure virtual) for the later ONNX implementation
- `src/*.cpp` stubs throw `std::logic_error("not implemented: see MILESTONES C-track")`.
- `src/main.cpp` prints a not-implemented message and returns 0.
- `tests/test_main.cpp`: a single passing smoke test (instantiates nothing that throws) so CTest is green.

## 9. Initialisation steps (M0 checklist for the agent)

1. `git init`; create the layout from §5 with placeholder files where content comes later.
2. Add `LICENSE`, `.gitignore`, `.editorconfig`, `README.md`, `justfile`.
3. Copy this plan, `MILESTONES.md`, and `CLAUDE.md` into place.
4. Write `docs/decisions/0001-language-split.md` (Python reference sidecar → C++ port; Rust core; process boundary via protocol).
5. Python: `uv init --package`, set the Python pin (D4), add dependencies, set up the package layout with empty modules that each have a module docstring naming their milestone. Add `scripts/download_models.py` (downloads `face_landmarker.task` into `gaze-py/models/`; the URL goes in a constant with a comment to verify it against MediaPipe's current docs).
6. Protocol: write both schemas and the three fixtures; add `tests/test_protocol.py` that validates every fixture.
7. Rust: create the workspace and crates per §8.1.
8. C++: create the CMake project per §8.2.
9. CI workflow per §6.
10. Run `just check-all` locally. Everything is green (Rust tests may be `ignored`; that counts as green).
11. Commit as `chore: initialise repository (M0)`; tick M0 in MILESTONES.md and add a log entry.

## 10. Out of scope for v1

- Multi-monitor gaze.
- Touch/pen or mobile.
- Remote or networked clients (the socket binds to localhost only).
- Storing or uploading any face imagery outside `recordings/`.
- Vision-based element detection for apps with no accessibility tree (noted as a future idea).
