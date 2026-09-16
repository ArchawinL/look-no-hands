# Rust (rs-*) and C++ (cpp-*) recipes arrive with their skeletons.

py-sync:
    cd gaze-py && uv sync

py-test:
    cd gaze-py && uv run pytest -m "not hardware"

py-lint:
    cd gaze-py && uv run ruff check && uv run ruff format --check && uv run mypy --strict src

check-all: py-lint py-test
