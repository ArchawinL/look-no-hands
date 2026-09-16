# 0001 — Language split

**Context.** The tool needs a webcam gaze pipeline (heavy ML and vision libraries,
fast iteration) and a native overlay app (OS accessibility APIs, global hotkeys,
click-through windows). The human also wants to learn Rust and C++.

**Decision.**
- Gaze sidecar: Python reference implementation (`gaze-py/`), agent-owned.
- Core app: Rust (`core-rs/`), human-owned.
- Later C++ port of the sidecar (`gaze-cpp/`), human-owned, checked against Python parity vectors.
- The boundary is a process boundary: protocol v1 over localhost TCP (`protocol/`).

**Consequences.**
- Either sidecar can serve the Rust app unchanged, provided both pass the shared fixtures.
- Protocol changes need a version bump and human approval.
- Pure logic in Python stays free of OpenCV/MediaPipe imports so it is testable and portable.
