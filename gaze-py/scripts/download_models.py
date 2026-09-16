"""Download the MediaPipe face landmarker model into gaze-py/models/."""

import sys
import urllib.request
from pathlib import Path

# Verify against https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
)
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "face_landmarker.task"


def main() -> int:
    if MODEL_PATH.exists() and "--force" not in sys.argv:
        print(f"already present: {MODEL_PATH} (use --force to re-download)")
        return 0
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = MODEL_PATH.with_suffix(".part")
    print(f"downloading {MODEL_URL}")
    urllib.request.urlretrieve(MODEL_URL, tmp)
    tmp.replace(MODEL_PATH)
    print(f"saved {MODEL_PATH} ({MODEL_PATH.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
