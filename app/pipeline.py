"""
pipeline.py – Main invoice processing pipeline.

Flow:
  Image
    └─► preprocess
          └─► extract (with retry)        ← invalid JSON silently dropped
                └─► verify + confidence
                      ├─ HIGH confidence + verified  →  MongoDB processed collection
                      └─ LOW confidence / unverified →  MongoDB GridFS  (image only)
"""

from config import CONFIDENCE_THRESHOLD
from database import save_invalid_file, save_valid_invoice
from extraction import extract_with_retry
from preprocessing import preprocess_image
from review import send_to_review
from verification import compute_confidence, verify_output


def process_invoice(image_path: str) -> dict:
    """
    Run the full extraction pipeline for a single invoice image.

    Returns a status dict with keys:
      - status      : "success" | "failed" | "low_confidence"
      - confidence  : float (when available)
      - mongo_id    : str  (on success)
      - data        : dict (on success)
      - message     : str  (on failure)
    """
    print(f"\nProcessing: {image_path}")

    # ── Step 1: Preprocess ────────────────────────────────────────────────────
    processed_img = preprocess_image(image_path)
    if processed_img is None:
        reason = "Could not preprocess image"
        send_to_review(image_path)
        save_invalid_file(image_path, reason=reason)
        return {"status": "failed", "message": reason}

    # ── Step 2: Extract (invalid JSON never leaves extract_with_retry) ────────
    result = extract_with_retry(processed_img)
    if not result:
        reason = "Extraction failed after all retries"
        send_to_review(image_path)
        save_invalid_file(image_path, reason=reason)
        return {"status": "failed", "message": reason}

    # ── Step 3: Verify ────────────────────────────────────────────────────────
    verified   = verify_output(processed_img, result)

    # ── Step 4: Confidence ────────────────────────────────────────────────────
    confidence = compute_confidence(result, verified)

    # ── Step 5: Route to MongoDB ──────────────────────────────────────────────
    if confidence < CONFIDENCE_THRESHOLD or not verified:
        reason = f"Low confidence ({confidence}) or failed verification"
        send_to_review(image_path, result.model_dump_json())
        save_invalid_file(image_path, reason=reason, confidence=confidence)
        return {
            "status":     "low_confidence",
            "confidence": confidence,
            "verified":   verified,
        }

    # ── Valid invoice ─────────────────────────────────────────────────────────
    mongo_id = save_valid_invoice(image_path, result, confidence)
    return {
        "status":     "success",
        "confidence": confidence,
        "mongo_id":   mongo_id,
        "data":       result.model_dump(),
    }
