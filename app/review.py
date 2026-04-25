"""
review.py – Local review fallback.

Copies invoice images (and optional JSON sidecars) to the reviews folder
so operators can manually inspect failed or low-confidence extractions.
"""

import os
import shutil

from config import REVIEW_FOLDER


def send_to_review(image_path: str, result_json: str | None = None) -> None:
    """
    Copy the image (and an optional valid-JSON sidecar) to REVIEW_FOLDER.

    `result_json` should only be passed when it contains a *valid*
    serialised Invoice — never a raw LLM response string.
    """
    os.makedirs(REVIEW_FOLDER, exist_ok=True)

    filename    = os.path.basename(image_path)
    destination = os.path.join(REVIEW_FOLDER, filename)
    shutil.copy(image_path, destination)

    if result_json:
        base = os.path.splitext(filename)[0]
        with open(os.path.join(REVIEW_FOLDER, base + ".json"), "w") as f:
            f.write(result_json)

    print(f"  [Review] Copied to local reviews folder: {destination}")
