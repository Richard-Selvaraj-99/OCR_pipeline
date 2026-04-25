"""
preprocessing.py – Image preprocessing before LLM extraction.

Steps applied to every invoice image:
  1. 2× upscale       – helps the vision LLM read small text
  2. Grayscale         – removes colour noise, reduces bytes sent to model
  3. CLAHE             – boosts contrast on faded/low-contrast invoices
     without blowing out bright areas

`fastNlMeansDenoisingColored` was intentionally excluded: it is designed
for Tesseract-style OCR pipelines, is very slow (2-5 s/image), and can
smear fine text that a vision LLM handles natively.
"""

import os

import cv2

from config import (
    CLAHE_CLIP_LIMIT,
    CLAHE_TILE_GRID,
    PROCESSED_FOLDER,
    UPSCALE_FACTOR,
)


def preprocess_image(image_path: str) -> str | None:
    """
    Preprocess an invoice image and write the result to PROCESSED_FOLDER.

    Returns the path to the processed image, or None if the image could
    not be read.
    """
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

    image = cv2.imread(image_path)
    if image is None:
        print(f"Warning: Could not read image: {image_path}")
        return None

    # Step 1 – Upscale
    image = cv2.resize(
        image, None,
        fx=UPSCALE_FACTOR, fy=UPSCALE_FACTOR,
        interpolation=cv2.INTER_CUBIC,
    )

    # Step 2 – Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 3 – CLAHE
    clahe    = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_GRID)
    enhanced = clahe.apply(gray)

    filename       = f"processed_{os.path.basename(image_path)}"
    processed_path = os.path.join(PROCESSED_FOLDER, filename)
    cv2.imwrite(processed_path, enhanced)

    return processed_path
