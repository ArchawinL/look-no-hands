# look-no-hands gaze sidecar (Python)

Reference implementation of the webcam gaze and wink sidecar. See `../docs/PLAN.md`.

```sh
uv sync
uv run python scripts/download_models.py   # into models/ (gitignored)
uv run python -m look_no_hands --help
uv run pytest -m "not hardware"
```
