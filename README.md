# look-no-hands

Hands-free, mouseless input: a Homerow-style hint overlay (Rust, `core-rs/`) driven by
keyboard or by a webcam gaze and wink sidecar (Python, `gaze-py/`). The two talk over
`127.0.0.1:47800` using newline-delimited JSON ([protocol v1](protocol/)).

Status: early. See [docs/PLAN.md](docs/PLAN.md) and [docs/MILESTONES.md](docs/MILESTONES.md).

## Quick start (gaze sidecar)

Requires [uv](https://docs.astral.sh/uv/). [just](https://just.systems/) is optional.

```sh
cd gaze-py
uv sync
uv run python scripts/download_models.py
uv run python -m look_no_hands doctor
uv run python -m look_no_hands viewer
```

Checks: `just check-all`, or run the commands in the `justfile` by hand.

## Privacy

`recordings/` holds face video and is gitignored. Nothing leaves the machine; the sidecar
binds to localhost only.

## License

MIT
