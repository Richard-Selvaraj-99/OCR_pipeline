"""
verification.py – Output verification and confidence scoring.
"""

import re
from datetime import datetime

from models import Invoice


def verify_output(image_path: str, data: Invoice) -> bool:
    """
    Run a set of sanity checks against an extracted Invoice.

    Returns True only when all checks pass.
    """
    checks: list[bool] = []

    # Tax / subtotal consistency
    if data.tax is not None and data.items:
        if data.tax > 1:
            implied_subtotal = data.expenses - data.tax
            checks.append(implied_subtotal > 0)

    # Item count
    checks.append(0 < len(data.items) <= 50)

    # Reasonable expense range
    checks.append(0 < data.expenses < 1_000_000)

    # Date parsability
    if data.date:
        try:
            datetime.strptime(data.date, "%Y-%m-%d")
            checks.append(True)
        except ValueError:
            checks.append(False)

    return all(checks) if checks else False


def compute_confidence(data: Invoice, verified: bool) -> float:
    """
    Compute a [0, 1] confidence score for an extracted invoice.

    Weights:
      expenses present and > 0   → 0.40
      tax present                → 0.10
      date in YYYY-MM-DD format  → 0.15
      title non-empty            → 0.10
      items non-empty            → 0.15
      passed verify_output       → 0.10
    """
    score    = 0.0
    possible = 0.0

    possible += 0.40
    if data.expenses and data.expenses > 0:
        score += 0.40

    possible += 0.10
    if data.tax is not None:
        score += 0.10

    possible += 0.15
    if data.date and re.match(r"\d{4}-\d{2}-\d{2}", data.date):
        score += 0.15

    possible += 0.10
    if data.title and len(data.title.strip()) > 2:
        score += 0.10

    possible += 0.15
    if data.items and len(data.items) > 0:
        score += 0.15

    possible += 0.10
    if verified:
        score += 0.10

    return round(score / possible, 2) if possible else 0.0
