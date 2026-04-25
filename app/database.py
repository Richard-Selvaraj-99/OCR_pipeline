"""
database.py – MongoDB connection and write helpers.

Two storage areas inside the `invoices` database:
  - invoices.processed   : valid invoice JSON documents
  - GridFS invalid_files : raw image binaries for failed / low-confidence invoices
"""

import os
from datetime import datetime, timezone

import gridfs
from bson import ObjectId
from pymongo import MongoClient

from config import DB_NAME, MONGO_URI
from models import Invoice


# ── Singleton connection ──────────────────────────────────────────────────────

def get_db():
    """Return (db, processed_col, invalid_fs) for the invoices database."""
    client        = MongoClient(MONGO_URI)
    db            = client[DB_NAME]
    processed_col = db["processed"]
    invalid_fs    = gridfs.GridFS(db, collection="invalid_files")
    return db, processed_col, invalid_fs


# Module-level singletons (initialised once on import)
_db, processed_col, invalid_fs = get_db()


# ── Write helpers ─────────────────────────────────────────────────────────────

def save_valid_invoice(image_path: str, data: Invoice, confidence: float) -> str:
    """
    Insert a successfully-extracted invoice as a JSON document into
    ``invoices.processed``.

    Returns the inserted document's _id as a string.
    """
    document = {
        "source_file":  os.path.basename(image_path),
        "confidence":   confidence,
        "extracted_at": datetime.now(timezone.utc),
        "invoice":      data.model_dump(),   # plain dict — never raw JSON strings
    }
    result = processed_col.insert_one(document)
    print(f"  [MongoDB] Valid invoice saved → _id: {result.inserted_id}")
    return str(result.inserted_id)


def save_invalid_file(image_path: str, reason: str, confidence: float = 0.0) -> str:
    """
    Store the raw invoice image in GridFS (``invalid_files`` bucket).
    Metadata records the failure reason.

    NOTE: No JSON payload is written — only the binary image.

    Returns the GridFS file _id as a string.
    """
    filename = os.path.basename(image_path)
    with open(image_path, "rb") as f:
        file_id = invalid_fs.put(
            f,
            filename=filename,
            metadata={
                "reason":      reason,
                "confidence":  confidence,
                "uploaded_at": datetime.now(timezone.utc),
                "source_path": image_path,
            },
        )
    print(f"  [MongoDB] Invalid file stored in GridFS → _id: {file_id}  reason: {reason}")
    return str(file_id)


# ── Query helpers ─────────────────────────────────────────────────────────────

def list_valid_invoices(limit: int = 10) -> list[dict]:
    """Return the most recently processed valid invoices."""
    docs = list(processed_col.find().sort("extracted_at", -1).limit(limit))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        if "extracted_at" in doc:
            doc["extracted_at"] = doc["extracted_at"].isoformat()
    return docs


def list_invalid_files(limit: int = 10) -> list[dict]:
    """Return metadata for files stored in the invalid GridFS bucket."""
    results = []
    for gf in invalid_fs.find().sort("uploadDate", -1).limit(limit):
        meta = gf.metadata or {}
        results.append(
            {
                "_id":        str(gf._id),
                "filename":   gf.filename,
                "reason":     meta.get("reason"),
                "confidence": meta.get("confidence"),
                "upload_date": gf.upload_date.isoformat() if gf.upload_date else None,
            }
        )
    return results


def retrieve_invalid_image(file_id_str: str, save_to: str = ".") -> str:
    """
    Download an invalid invoice image from GridFS back to disk.

    Usage:
        retrieve_invalid_image("64abc123...", save_to="/tmp")
    """
    gf       = invalid_fs.get(ObjectId(file_id_str))
    out_path = os.path.join(save_to, gf.filename)
    with open(out_path, "wb") as f:
        f.write(gf.read())
    print(f"Retrieved: {out_path}")
    return out_path
