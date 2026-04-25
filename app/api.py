"""
api.py – FastAPI REST interface for the Invoice Extractor pipeline.

Endpoints:
  POST /upload/                  – process one or more invoice images
  GET  /valid/                   – list valid invoices from MongoDB
  GET  /invalid/                 – list invalid file metadata from GridFS
  GET  /invalid/image/{file_id}  – retrieve a raw invalid invoice image
"""

import os
import shutil

import uvicorn
from bson import ObjectId
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response
from typing import List

from config import API_HOST, API_PORT
from database import invalid_fs, list_invalid_files, list_valid_invoices
from pipeline import process_invoice

app = FastAPI(title="Invoice Pipeline API", version="1.0.0")


# ── Upload & process ──────────────────────────────────────────────────────────

@app.post("/upload/", summary="Upload and process invoice images")
async def upload_invoices(files: List[UploadFile] = File(...)):
    """Accept one or more image files, run the full pipeline, return results."""
    results = []
    for file in files:
        temp_path = f"temp_{file.filename}"
        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            res = process_invoice(temp_path)
            results.append({"filename": file.filename, "result": res})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    return {"results": results}


# ── Query endpoints ───────────────────────────────────────────────────────────

@app.get("/valid/", summary="List valid invoices")
def get_valid(limit: int = 20):
    """Return the most recently processed valid invoices."""
    return list_valid_invoices(limit=limit)


@app.get("/invalid/", summary="List invalid invoice metadata")
def get_invalid(limit: int = 20):
    """Return metadata for files stored in the invalid GridFS bucket."""
    return list_invalid_files(limit=limit)


@app.get("/invalid/image/{file_id}", summary="Retrieve an invalid invoice image")
def get_invalid_image(file_id: str):
    """Stream a raw invalid invoice image from GridFS."""
    gf = invalid_fs.get(ObjectId(file_id))
    return Response(content=gf.read(), media_type="image/jpeg")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("api:app", host=API_HOST, port=API_PORT, reload=True)
