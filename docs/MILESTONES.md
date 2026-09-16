# look-no-hands — Milestones & Stories

Read [`PLAN.md`](./PLAN.md) first for architecture, layout, and the protocol.

## How to use this file

**Everyone**
- Work on **one story at a time**. A story is done only when every acceptance criterion is met.
- Criteria tagged **(auto)** are checked by tests or commands. Criteria tagged **(manual)** need a human at a real webcam and screen; the agent must ask the human to verify them and must not tick them itself.
- When a story is done: tick it on the status board, then add a row to the **Progress log** at the bottom.
- If a story turns out to be wrong or too big, split or edit it and note why in the log. Don't silently skip criteria.

**Agent (Claude Code)**
- Implement only stories marked **Owner: agent**.
- For **Owner: human** stories, only review, explain, or give hints, unless the human explicitly says "implement this one".
- Branch per story: `p3-protocol-transport`, etc. Commit message prefix: the story ID, e.g. `P3: add TCP transport`.

**Human**
- Human stories list a **Learning focus** so you know which chapter or docs to read before starting.
- Ask the agent for review with: "Review my R2 against its acceptance criteria. Don't rewrite it; point out problems and explain why."

## Status board

**Foundation**
- [ ] M0 — Initialise repository (agent)

**P-track — Python gaze sidecar (agent)**
- [ ] P1 — Camera, landmarks, debug viewer, `doctor`
- [ ] P2 — Feature extraction, head pose, left/right verification
- [ ] P3 — Protocol v1, TCP transport, `listen` tool
- [ ] P4 — One Euro filter and time-indexed ring buffer
- [ ] P5 — Calibration (9-point) and profiles
- [ ] P6 — Validation board and accuracy report
- [ ] P7 — Wink detector and wink setup
- [ ] P8 — Sidecar `run` command (full pipeline)
- [ ] P9 — Recording, replay, and parity vectors
- [ ] P10 — Snap demo (end-to-end concept proof)
- [ ] P11 — Hardening, latency, docs
- [ ] P12 — *(stretch)* Fixation detection and dwell messages

**R-track — Rust core app (human, learning Rust)**
- [ ] R1 — Geometry and hint labels
- [ ] R2 — Region filter and fake provider
- [ ] R3 — Real element provider (primary OS from decision D1)
- [ ] R4 — Global hotkey and key capture
- [ ] R5 — Overlay window
- [ ] R6 — Activation and keyboard selector → **usable Homerow-style tool**
- [ ] R7 — Gaze client
- [ ] R8 — Gaze region and wink selector

**C-track — C++ gaze port (human, learning C++; start after P9 and R6)**
- [ ] C1 — Catch2 and One Euro filter (parity)
- [ ] C2 — Calibration with Eigen (parity)
- [ ] C3 — Wink detector (parity)
- [ ] C4 — Protocol output and TCP server
- [ ] C5 — Camera and face detection with OpenCV
- [ ] C6 — Landmark model via ONNX Runtime
- [ ] C7 — Blendshapes and full replay parity

**Suggested order:** M0 → P1–P5 → P6–P10 → P11. The human can start R1 any time after M0 and continue the R-track in parallel. The C-track starts once P9 (parity vectors) and R6 are done.

---

## M0 — Initialise repository
**Owner:** agent · **Depends on:** nothing

**Goal:** A repo matching PLAN.md §5 in which every part builds and CI is green, and nothing beyond skeletons is implemented.

**Tasks:** Follow PLAN.md §9 exactly.

**Acceptance**
- (auto) `just check-all` passes locally. Rust tests may be `ignored`.
- (auto) CI passes on all jobs.
- (auto) `pytest` validates every fixture in `protocol/fixtures/` against its schema.
- (auto) `cargo test` lists the ignored R1/R2 tests, each with a reason string naming its milestone.
- (auto) `ctest` runs one passing smoke test with no vcpkg packages installed.
- (manual) Human confirms open decisions D1–D6 are recorded in `docs/decisions/` or explicitly deferred.

---

## P-track — Python gaze sidecar

### P1 — Camera, landmarks, debug viewer, `doctor`
**Owner:** agent · **Depends on:** M0

**Goal:** See MediaPipe landmarks and blendshapes live, and diagnose setup problems.

**Tasks**
- `camera.py`: open a camera by index, request 640×480 at 30 fps, and yield `(frame, t_ms)` using a monotonic clock. Report the actual resolution and FPS.
- `landmarks.py`: wrap MediaPipe `FaceLandmarker` in VIDEO running mode with `output_face_blendshapes=True` and `output_facial_transformation_matrixes=True`, `num_faces=1`. Return a typed result: 478 landmarks, a blendshape dict, a 4×4 transform, or `None` when no face is found.
- `tools/viewer.py`: draw iris and eye-contour landmarks, show `eyeBlinkLeft`/`eyeBlinkRight` as bars, and show FPS and processing time per frame.
- `doctor` subcommand checks: model file present, camera opens, a face is detected within 5 s, display size is readable. On macOS, print a hint about granting camera permission to the terminal app.

**Acceptance**
- (auto) Unit test: the landmark wrapper returns `None` for a blank frame (marked `hardware` if it needs the model file).
- (manual) Viewer runs at ≥ 25 fps on the human's laptop at 640×480.
- (manual) `doctor` output is clear when the camera is covered, the model is missing, or no face is visible.

### P2 — Feature extraction, head pose, left/right verification
**Owner:** agent · **Depends on:** P1

**Goal:** Turn landmarks into a stable feature vector, and settle which eye is "left" once and for all.

**Tasks**
- `features.py` computes a `FeatureVector` per frame:
  - For each eye: iris center relative to the eye corners, with horizontal offset normalised by eye width and vertical offset normalised by eyelid distance.
  - Eye openness per eye.
  - Head yaw, pitch, and roll in degrees, plus head translation, taken from the transformation matrix.
- Put landmark index constants in one place, with a comment citing where each index came from.
- Add a "which eye" check to the viewer: prompt "close your LEFT eye", record which blendshape and which landmark set respond, and print the result.
- Document the verified mapping in `docs/protocol.md`. Protocol `left` always means the user's left eye.

**Acceptance**
- (auto) Features are finite and roughly in the range −1.5 to 1.5 for a synthetic landmark set (fixture built in the test).
- (auto) Feature extraction is a pure function with no MediaPipe import, so it is unit-testable.
- (manual) The left/right check gives the correct result with the camera image both mirrored and unmirrored.
- (manual) Looking at the four screen corners with the head still produces visibly distinct feature values in the viewer.

### P3 — Protocol v1, TCP transport, `listen` tool
**Owner:** agent · **Depends on:** M0 (can run in parallel with P1–P2)

**Goal:** Messages exactly as specified in PLAN.md §7, sent to any number of local clients.

**Tasks**
- `protocol.py`: frozen dataclasses for `Gaze`, `Wink`, `Status`; `to_json_line()` and `from_json_line()`. Unknown fields are ignored when parsing.
- `transport.py`: a TCP server bound to `127.0.0.1` only. Accepts multiple clients. A slow client must never block the pipeline; drop that client's oldest messages and log a warning.
- `tools/listen.py`: connects and pretty-prints the stream, with a `--type` filter.
- Write `docs/protocol.md`, the human-readable spec.
- A `fake-stream` subcommand replays `protocol/fixtures/gaze_stream_basic.jsonl` on a loop, so the Rust R7 work doesn't need a camera.

**Acceptance**
- (auto) Round-trip tests for every message type; every message emitted validates against `gaze.schema.json`.
- (auto) Test: two clients connected, one never reads; the other still receives every message within 100 ms.
- (auto) The server refuses to bind to non-loopback addresses.
- (manual) `fake-stream` plus `listen` works in two terminals.

### P4 — One Euro filter and time-indexed ring buffer
**Owner:** agent · **Depends on:** M0

**Goal:** Jitter-free cursor movement without lag, plus the ability to ask "where was gaze 150 ms ago?".

**Tasks**
- `filters.py`: One Euro filter (Casiez et al., CHI 2012) with `min_cutoff`, `beta`, `d_cutoff`, and variable time steps. A 2D wrapper for x and y.
- `ringbuffer.py`: stores `(t_ms, value)`. Provides `at_or_before(t_ms)` and `mean_between(t0, t1)`, with a fixed capacity.

**Acceptance**
- (auto) With a constant input, the filter converges to it.
- (auto) On a step input, a higher `beta` gives less lag; the test asserts the ordering.
- (auto) Irregular time steps don't produce NaN or inf.
- (auto) Ring buffer edge cases: empty buffer, exact timestamp match, lookup older than capacity, wrap-around.

### P5 — Calibration (9-point) and profiles
**Owner:** agent · **Depends on:** P2, P4

**Goal:** Map feature vectors to screen coordinates, per user, saved to disk.

**Tasks**
- `calibration.py`:
  - Standardise the features, expand them to degree-2 polynomial terms, and fit a closed-form ridge regression, one model each for x and y.
  - `fit`, `predict`, `to_dict`, `from_dict`. Record a version number in the saved profile.
- `tools/calibrate.py`: a fullscreen window showing a 3×3 grid inset 10% from the edges.
  - For each point: an animated shrinking dot, a 600 ms settle time, then 800 ms of sample collection.
  - Reject outlier samples using median absolute deviation.
  - Show a "hold still / look here" prompt.
- Save profiles as JSON in the user config directory (via `platformdirs`), named `<profile>.json`, together with the screen size and camera index they were made for.
- Refuse to load a profile if the screen size doesn't match; tell the user to recalibrate.

**Acceptance**
- (auto) On synthetic data generated from a known quadratic mapping plus noise, predictions are within tolerance.
- (auto) A profile survives a save/load round trip unchanged.
- (auto) Loading a profile with a mismatched screen size raises a clear error.
- (manual) After calibrating, the viewer's gaze dot visibly follows the human's gaze across the screen.

### P6 — Validation board and accuracy report
**Owner:** agent · **Depends on:** P5

**Goal:** Measure real accuracy instead of guessing, using the same numbers discussed during planning.

**Tasks**
- `tools/validate.py` shows 13 targets that were not used in calibration, in random order, and collects filtered gaze samples for each.
- The report includes:
  - Accuracy: mean, median, and 90th-percentile error, in points.
  - Approximate error in degrees, using config values for screen diagonal (inches) and viewing distance (default 60 cm).
  - Precision: standard deviation of samples during each fixation.
  - Error broken down per 3×3 screen region.
- Save the report as JSON under `recordings/reports/` and print a readable summary.

**Acceptance**
- (auto) The points↔degrees conversion is unit-tested against a hand-calculated example.
- (manual) The human runs validation three times (good lighting, dim lighting, with glasses if relevant) and pastes the summaries into the Progress log. **These numbers set the default region radius used in P10 and R8.**

### P7 — Wink detector and wink setup
**Owner:** agent · **Depends on:** P4

**Goal:** Reliable left and right winks that ignore ordinary blinks, with the click position taken from gaze *before* the wink began.

**Tasks**
- `winks.py`: a state machine per eye using the blendshape scores.
  - A wink **starts** when one eye's score is ≥ `close_thr` while the other eye's is ≤ `open_thr`.
  - It is **accepted** if it lasts between `min_ms` and `max_ms` and the other eye stays open the whole time.
  - Both eyes closing at any point means it's a blink: reject it.
  - After an accepted wink, apply a `cooldown_ms`.
  - The emitted event includes the gaze position looked up at `onset − lookback_ms` from the ring buffer.
  - Defaults: `close_thr 0.5`, `open_thr 0.25`, `min_ms 120`, `max_ms 800`, `cooldown_ms 400`, `lookback_ms 150`.
- Winks must be optional. A `winks.enabled` setting turns detection off entirely.
- `tools/wink_setup.py`: guided capture of 5 blinks, 5 left winks, 5 right winks, and 10 s of relaxed viewing. Derive per-user thresholds, since one eye's closure partly lowers the other's score, and store them in the profile. If the user can't produce a clean wink on one side, record that and disable that side.

**Acceptance**
- (auto) Table-driven tests with synthetic score sequences cover: clean left wink, clean right wink, blink, a wink that's too short, one that's too long, a wink that turns into a blink, a second wink during cooldown, and a squint (both scores moderately high).
- (auto) The gaze position in an event comes from the lookback time, not the onset time.
- (manual) In 20 intentional winks per side, at least 18 are detected. In 2 minutes of normal reading, there are no false winks.

### P8 — Sidecar `run` command (full pipeline)
**Owner:** agent · **Depends on:** P3, P5, P7

**Goal:** The real sidecar that the Rust app will talk to.

**Tasks**
- `pipeline.py` chains camera → landmarks → features → calibration → filter → ring buffer → winks → transport. The pipeline takes its frame source as a parameter so that replay (P9) runs through the identical code.
- The `run` subcommand accepts `--profile`, `--camera`, `--port`, and `--no-winks`.
- Status handling:
  - `uncalibrated` if no profile loads.
  - `no_face` after 300 ms without a face; resume cleanly when the face returns and reset the filter.
  - Heartbeat every 1 s.
- Clean shutdown on Ctrl+C: release the camera and close sockets.
- Structured logging to stderr, with the level set by `--log-level`.

**Acceptance**
- (auto) The pipeline runs end to end with a fake frame source and fake landmark model, and the expected message sequence appears on a test client.
- (manual) `run` plus `listen` shows sensible gaze and wink messages for 5 minutes with no crash and no memory growth.

### P9 — Recording, replay, and parity vectors
**Owner:** agent · **Depends on:** P8

**Goal:** Deterministic sessions for debugging, and shared test vectors for the C++ port.

**Tasks**
- `record` subcommand writes to `recordings/<timestamp>/`:
  - `video.mp4`
  - `frames.jsonl` (frame timestamps)
  - `landmarks.jsonl` (478 points, blendshapes, transform)
  - `output.jsonl` (the protocol messages)
  - `meta.json` (camera, screen, profile, software versions)
- `replay` subcommand has two modes:
  - `--from video`: re-runs MediaPipe on the recorded video.
  - `--from landmarks`: skips the model; fully deterministic.
  Both run through `pipeline.py`.
- `scripts/export_parity_vectors.py` writes `protocol/fixtures/parity/` containing:
  - `one_euro.json`: filter parameters, input sequence, expected output sequence.
  - `calibration.json`: training samples, fitted coefficients, test inputs, expected predictions.
  - `winks.json`: score sequences and expected events.
- Commit a **small synthetic** `landmarks.jsonl` fixture, generated by a script. Never commit real face data unless the human explicitly approves it.
- Print a clear warning on `record` that recordings contain face video, and confirm `recordings/` is gitignored.

**Acceptance**
- (auto) Replaying the synthetic landmark fixture twice produces byte-identical `output.jsonl`.
- (auto) Parity vectors regenerate identically, and a test checks the Python implementation against them.
- (manual) Recording a real 30 s session and replaying it `--from landmarks` reproduces the recorded output.

### P10 — Snap demo (end-to-end concept proof)
**Owner:** agent · **Depends on:** P8

**Goal:** Prove the whole interaction in Python before any Rust exists, and measure whether it's usable.

**Tasks**
- `tools/snap_demo.py` opens a fullscreen window that draws fake targets, using `targets.schema.json` layouts. Provide three layouts:
  - `sparse_dialog`: a few large buttons.
  - `toolbar_dense`: many 28 pt icons in a row.
  - `web_page`: mixed links and buttons.
- On screen: the gaze dot, a region circle (radius from config; default taken from P6 results), and candidates inside the region highlighted.
- **Keyboard mode:** home-row labels drawn only for candidates in the region; typing a label selects that target.
  - Implement a simple prefix-free label generator **in Python only**. Do not port it to Rust; that's R1.
- **Wink mode:** the nearest candidate to the gaze point is highlighted; left wink = primary action, right wink = secondary.
- **Task mode:** the demo marks a random target to hit and logs time-to-select, whether the selection was correct, and how many candidates were in the region. It writes a summary per layout.

**Acceptance**
- (auto) The region filter and label generator are unit-tested, including "no label is a prefix of another".
- (manual) The human completes task mode on all three layouts in both modes and pastes the summaries into the Progress log.
- (manual) Human verdict recorded in the log: is it usable? What region radius feels right?

### P11 — Hardening, latency, docs
**Owner:** agent · **Depends on:** P9, P10

**Tasks**
- Measure latency from frame capture to message sent (median and p95) and include it in `status` as an optional `latency_ms` field. This is an allowed v1 addition.
- Quick re-center: look at the screen center and press a key to apply an offset correction without a full recalibration. Store it separately from the profile.
- Config file with documented defaults. `config show` and `config path` subcommands.
- `gaze-py/README.md`: setup, the calibration routine, troubleshooting (lighting, glasses, camera placement), and privacy notes.
- Finalise `docs/protocol.md` and confirm the fixtures match it.

**Acceptance**
- (auto) mypy strict and ruff are clean; test coverage of `src/` excluding `tools/` is ≥ 80%.
- (manual) The median latency is recorded in the Progress log.
- (manual) The human follows the README from a fresh clone and it works.

### P12 — *(stretch)* Fixation detection and dwell messages
**Owner:** agent · **Depends on:** P8

**Tasks:** A velocity-threshold fixation classifier (I-VT). Add an optional `fixation` message type (`start`/`end`, center point, duration), documented in the protocol as an optional type that clients may ignore. Add dwell mode to the snap demo.

**Acceptance:** (auto) Classifier tests on synthetic saccade/fixation sequences. (manual) Dwell selection works in the snap demo.

---

## R-track — Rust core app (human, learning)

The agent's role on these stories is to review, explain, and hint, and to write code only when explicitly asked. Each story names the Rust Book chapters to read first (doc.rust-lang.org/book).

### R1 — Geometry and hint labels
**Owner:** human · **Depends on:** M0
**Learning focus:** Book ch. 3–6 (basics, ownership, structs, enums), ch. 11 (tests). Rustlings up to `structs` and `enums`.
**Tasks:** Implement `Rect::center`, `Rect::intersects`, and `generate_labels`. Remove the `#[ignore]` from their tests.
**Acceptance:** (auto) The un-ignored tests pass, and `cargo clippy -- -D warnings` is clean. Add at least 2 tests of your own: zero targets, and more targets than one-letter labels can cover.
**Agent may help by:** explaining borrow-checker errors, suggesting iterator methods, reviewing.

### R2 — Region filter and fake provider
**Owner:** human · **Depends on:** R1
**Learning focus:** ch. 7 (modules), ch. 8 (collections), ch. 9 (errors), ch. 10 (traits). Add your first crates: `serde` and `serde_json`.
**Tasks:** Implement `filter_targets`. In `look-no-hands-platform`, create a `FakeProvider` that reads `protocol/fixtures/targets_sample.json`. `look-no-hands-app --fake` prints the targets inside a hard-coded circle.
**Acceptance:** (auto) Filter tests cover a target straddling the circle's edge, an empty list, and the full-screen region. (auto) A test parses the shared fixture.

### R3 — Real element provider
**Owner:** human · **Depends on:** R2, decision D1
**Learning focus:** reading docs.rs, `cfg` attributes, `anyhow`. Crate for your OS: `axuielement` (macOS), `uiautomation` (Windows), or `atspi` (Linux).
**Tasks:** `NativeProvider` for the frontmost window plus the menu bar and dock/taskbar. Skip elements that are hidden, zero-sized, or off-screen. Handle a missing permission with a clear message. On macOS, set `AXManualAccessibility` on Chromium/Electron apps.
**Acceptance:** (manual) `look-no-hands-app --list` prints sensible targets for Finder/Explorer, a browser, and one Electron app. (manual) Timing is printed; aim for < 150 ms in the frontmost window.

### R4 — Global hotkey and key capture
**Owner:** human · **Depends on:** R2
**Learning focus:** ch. 16 (threads, channels), ch. 13 (closures).
**Tasks:** Listen for a global hotkey on its own thread and send events to the main loop over a channel. While hint mode is active, capture keys; Esc cancels.
**Acceptance:** (manual) The hotkey toggles a "hint mode on/off" log line from any app. Typed keys are captured only while hint mode is active.

### R5 — Overlay window
**Owner:** human · **Depends on:** R4
**Learning focus:** `winit` event loop, main-thread rules on macOS, drawing (e.g. `tiny-skia` + `softbuffer`, or `egui`).
**Tasks:** A transparent, always-on-top, click-through, borderless window covering the screen that draws labels at given rectangles.
**Acceptance:** (manual) Labels align with the R3 targets at your display scaling. Mouse clicks pass through the overlay.
**Note:** Expect this to be the hardest R story. Ask the agent for help early rather than late.

### R6 — Activation and keyboard selector → usable tool
**Owner:** human · **Depends on:** R3, R5
**Learning focus:** enums with data, `match`, trait objects.
**Tasks:** Implement `Selector` for the keyboard. Activate targets with the element's native press action, falling back to a synthetic click at the center. Re-read the element's position just before clicking.
**Acceptance:** (manual) Daily-drivable: hotkey → labels → type → the right thing gets clicked, in at least 3 different apps. 🎉

### R7 — Gaze client
**Owner:** human · **Depends on:** R6, P3 (`fake-stream`)
**Learning focus:** `std::net::TcpStream`, `BufRead::lines`, serde enums with `#[serde(tag = "type")]`.
**Tasks:** Connect to the sidecar on a background thread, parse protocol v1 into `GazeMessage`, ignore unknown fields and types, and reconnect with backoff.
**Acceptance:** (auto) Tests parse every line of every fixture in `protocol/fixtures/`. (manual) Works against `fake-stream` and then against a real `run`.

### R8 — Gaze region and wink selector
**Owner:** human · **Depends on:** R7, P10 verdict
**Tasks:**
- Hint mode uses a gaze circle as the region, with the radius taken from the P6/P10 findings.
- In wink mode, highlight the nearest candidate; wink events select it using the wink's locked `x`/`y`.
- Settings choose between keyboard, wink, and both. Fall back to full-screen hints when the status isn't `tracking`.
**Acceptance:** (manual) The P10 task-mode results are reproduced in real apps, with similar success rates.

---

## C-track — C++ gaze port (human, learning)

Rules: port **from** the Python reference and check every step against `protocol/fixtures/parity/`. Use the `debug-asan` preset while developing. The agent's role is review, explanation, and build-system help.

### C1 — Catch2 and One Euro filter (parity)
**Learning focus:** classes, `const`, headers vs sources, CMake targets, vcpkg manifests.
**Tasks:** Add `catch2` to `vcpkg.json` and replace the smoke test. Implement `OneEuroFilter`.
**Acceptance:** (auto) Matches `one_euro.json` within 1e-9. Clean under ASan and UBSan.

### C2 — Calibration with Eigen (parity)
**Learning focus:** Eigen matrices, value semantics, `std::optional`, file I/O, `nlohmann-json`.
**Acceptance:** (auto) Predictions match `calibration.json` within 1e-6, and C++ can load profiles saved by Python.

### C3 — Wink detector (parity)
**Learning focus:** `enum class`, state machines, `<chrono>`.
**Acceptance:** (auto) Emits exactly the events in `winks.json`.

### C4 — Protocol output and TCP server
**Learning focus:** sockets (e.g. standalone Asio), threads, RAII.
**Acceptance:** (auto) Emitted lines validate against the schema, checked by running the Python validator in CTest. (manual) The Rust app from R7 works unchanged against the C++ server running in fake-stream mode.

### C5 — Camera and face detection with OpenCV
**Learning focus:** `cv::VideoCapture`, `cv::Mat`, `cv::FaceDetectorYN`.
**Acceptance:** (manual) The debug window shows a face box at ≥ 25 fps.

### C6 — Landmark model via ONNX Runtime
**Learning focus:** ONNX Runtime C++ API, preprocessing, coordinate transforms.
**Tasks:** Extract the landmark model from `face_landmarker.task` (a bundle of models) and convert it to ONNX, documenting the steps in `gaze-cpp/README.md`. Implement `LandmarkModel`: crop, run the model, map results back to frame coordinates.
**Acceptance:** (auto/manual) On a recorded session's video, the mean landmark distance from Python's `landmarks.jsonl` is within an agreed tolerance (set it after a first measurement and record it in the log).

### C7 — Blendshapes and full replay parity
**Acceptance:** (manual) `look-no-hands-gaze replay` on a recorded session produces gaze within a tolerance of Python's `output.jsonl` and the same wink events.

---

## Progress log

Newest first. One row per completed story, split story, or notable finding (accuracy numbers, verdicts, decisions).

| Date | Story | Who | Notes |
|---|---|---|---|
| | | | |
