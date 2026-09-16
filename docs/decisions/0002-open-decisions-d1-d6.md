# 0002 — Open decisions D1–D6 (PLAN §4)

**Context.** PLAN §4 lists six decisions to settle during M0.

**Decision.**
| # | Decision | Status |
|---|---|---|
| D1 | Primary dev OS | Windows 11 (inferred from the dev machine; human to confirm before R3) |
| D2 | Project name | `look-no-hands`; Python package `look_no_hands`; crates `look-no-hands-*` |
| D3 | License | MIT |
| D4 | Python pin | 3.12 (`mediapipe` 1.0.1 wheel verified on win_amd64, cp312) |
| D5 | IPC | TCP `127.0.0.1:47800`, newline-delimited JSON |
| D6 | Coordinates | Logical points, primary display, origin top-left |

**Consequences.** M0 is done in a Python-only slice first; the Rust and C++ skeletons are
deferred until the human starts those tracks.
