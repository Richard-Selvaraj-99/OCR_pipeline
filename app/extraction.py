"""
extraction.py – LLM-based invoice data extraction via Ollama.

Handles:
  - The extraction prompt
  - Calling the Qwen vision model
  - JSON + Pydantic validation
  - Business-rule validation
  - Retry logic (invalid JSON is dropped here and never propagates further)
"""

import json
import re

import ollama
from pydantic import ValidationError

from config import MAX_RETRIES, OLLAMA_MODEL
from models import Invoice


# ── Prompt ────────────────────────────────────────────────────────────────────

PROMPT = """
You are an information extraction system.

Extract the following fields from the invoice image:

{
  "title": string | null,
  "tax": number | null,
  "expenses": number,
  "date": string | null,
  "items": list[string]
}

CRITICAL DATE RULE:
If the date on the invoice is "12/05/24", "May 12, 2024", or "12-05-2024",
you MUST convert it to "2024-05-12" — always return date as YYYY-MM-DD.
If the year is missing, assume 2026.

STRICT RULES:
- Return ONLY valid JSON
- Do NOT guess values
- If unsure, return null
- expenses must be FINAL TOTAL
- tax must be numeric
- date format: YYYY-MM-DD
- items must be short descriptions
"""


# ── LLM call ──────────────────────────────────────────────────────────────────

def call_qwen(image_path: str) -> str:
    """Send the invoice image to Qwen via Ollama and return the raw response."""
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role":    "user",
                "content": PROMPT,
                "images":  [image_path],
            }
        ],
        format="json",
    )
    return response["message"]["content"]


# ── Validation ────────────────────────────────────────────────────────────────

def validate_json(response_text: str) -> Invoice | None:
    """
    Parse the LLM response and validate it against the Invoice model.

    Returns an Invoice on success, or None if the JSON is invalid or
    the schema does not match.  Invalid JSON strings are *never* passed
    further downstream.
    """
    try:
        data = json.loads(response_text)
        return Invoice.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"  JSON/validation error: {e}")
        return None


def business_validation(data: Invoice) -> bool:
    """Apply lightweight business rules to an extracted invoice."""
    if data.expenses <= 0:
        return False
    if data.tax is not None and data.tax < 0:
        return False
    if data.date:
        if not re.match(r"\d{4}-\d{2}-\d{2}", data.date):
            return False
    return True


# ── Retry wrapper ─────────────────────────────────────────────────────────────

def extract_with_retry(image_path: str, max_retries: int = MAX_RETRIES) -> Invoice | None:
    """
    Attempt extraction up to `max_retries` times.

    Returns a validated Invoice on success, or None when all attempts fail.
    """
    for attempt in range(max_retries):
        raw       = call_qwen(image_path)
        validated = validate_json(raw)       # invalid JSON → None, never stored
        if validated and business_validation(validated):
            print(f"  Extraction succeeded on attempt {attempt + 1}")
            return validated
        print(f"  Retrying... attempt {attempt + 1}")
    return None
