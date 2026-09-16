import json
from pathlib import Path

import pytest
from conftest import FIXTURES, REPO_ROOT
from jsonschema import Draft202012Validator

SCHEMAS = REPO_ROOT / "protocol"


def validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


GAZE = validator("gaze.schema.json")
TARGETS = validator("targets.schema.json")


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("*.jsonl")), ids=lambda p: p.name)
def test_jsonl_fixture_validates(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines
    for n, line in enumerate(lines, 1):
        errors = list(GAZE.iter_errors(json.loads(line)))
        assert not errors, f"{path.name}:{n}: {errors[0].message}"


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("targets_*.json")), ids=lambda p: p.name)
def test_targets_fixture_validates(path: Path) -> None:
    TARGETS.validate(json.loads(path.read_text(encoding="utf-8")))


def test_schema_rejects_bad_messages() -> None:
    bad = [
        {"v": 2, "type": "gaze", "t_ms": 0, "x": 0, "y": 0, "conf": 1},
        {"v": 1, "type": "gaze", "t_ms": 0, "x": 0, "y": 0},
        {
            "v": 1,
            "type": "wink",
            "t_ms": 0,
            "eye": "both",
            "x": 0,
            "y": 0,
            "lock_t_ms": 0,
            "duration_ms": 1,
        },
        {"v": 1, "type": "status", "t_ms": -1, "state": "tracking"},
        {"v": 1, "type": "status", "t_ms": 0, "state": "tracking", "typo": 1},
    ]
    for msg in bad:
        assert not GAZE.is_valid(msg), msg
