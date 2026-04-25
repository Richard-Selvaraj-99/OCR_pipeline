"""
models.py – Pydantic models for invoice data validation.
"""

from typing import List, Optional

from pydantic import BaseModel


class Invoice(BaseModel):
    title:    Optional[str]
    tax:      Optional[float]
    expenses: float
    date:     Optional[str]   # YYYY-MM-DD
    items:    List[str]
