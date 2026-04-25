"""
config.py – Central configuration for the Invoice Extractor pipeline.
Edit values here; all other modules import from this file.
"""

# ── MongoDB ──────────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017"   # Change for Atlas / remote host
DB_NAME   = "invoices"

# ── Local fallback folders ────────────────────────────────────────────────────
REVIEW_FOLDER    = "reviews"
PROCESSED_FOLDER = "processed"

# ── LLM ──────────────────────────────────────────────────────────────────────
OLLAMA_MODEL   = "qwen3.5:4b"
MAX_RETRIES    = 2

# ── Confidence threshold ──────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.85

# ── Image preprocessing ───────────────────────────────────────────────────────
UPSCALE_FACTOR   = 2               # 2× upscale before LLM
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID  = (8, 8)

# ── FastAPI ───────────────────────────────────────────────────────────────────
API_HOST = "127.0.0.1"
API_PORT = 8000
