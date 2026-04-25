# Invoice Extractor

Extract structured data from invoice images using a local vision LLM (Qwen via Ollama), validate the results, and store them in MongoDB.

## Project structure

```
invoice_extractor/
├── config.py          # All tuneable settings in one place
├── models.py          # Pydantic Invoice model
├── preprocessing.py   # OpenCV image preprocessing
├── extraction.py      # Ollama/Qwen LLM call, JSON validation, retry logic
├── verification.py    # Sanity checks + confidence scoring
├── review.py          # Local fallback folder for manual review
├── database.py        # MongoDB connection, read/write helpers
├── pipeline.py        # End-to-end orchestration
├── api.py             # FastAPI REST interface
├── app.py             # Streamlit dashboard
├── main.py            # CLI entry point
└── requirements.txt
```

## Prerequisites

- Python 3.11+
- MongoDB running on `localhost:27017` (or update `MONGO_URI` in `config.py`)
- [Ollama](https://ollama.com) running with the `qwen3.5:4b` model pulled:
  ```
  ollama pull qwen3.5:4b
  ```

## Installation

```bash
pip install -r requirements.txt
```

> The `python-multipart` package is required by FastAPI for file uploads.

## Usage

### CLI – process images directly

```bash
# Single invoice
python main.py path/to/invoice.jpg

# Whole folder
python main.py path/to/invoices/

# Inspect MongoDB records
python main.py --list
```

### REST API

```bash
python api.py
# → http://127.0.0.1:8000/docs  (Swagger UI)
```

| Method | Endpoint                      | Description                            |
|--------|-------------------------------|----------------------------------------|
| POST   | `/upload/`                    | Upload and process invoice image(s)    |
| GET    | `/valid/`                     | List valid invoices from MongoDB       |
| GET    | `/invalid/`                   | List invalid file metadata from GridFS |
| GET    | `/invalid/image/{file_id}`    | Download a raw invalid invoice image   |

### Streamlit dashboard

Start the API first, then:

```bash
streamlit run app.py
```

## Configuration

All tuneable values live in `config.py`:

| Setting               | Default              | Description                          |
|-----------------------|----------------------|--------------------------------------|
| `MONGO_URI`           | `mongodb://localhost` | MongoDB connection string            |
| `OLLAMA_MODEL`        | `qwen3.5:4b`         | Vision model used for extraction     |
| `MAX_RETRIES`         | `2`                  | LLM retry attempts per image         |
| `CONFIDENCE_THRESHOLD`| `0.85`               | Minimum score to accept an invoice   |
| `UPSCALE_FACTOR`      | `2`                  | Image upscale multiplier             |

## Pipeline flow

```
Image
  └─► preprocess (upscale → grayscale → CLAHE)
        └─► extract with retry  ← invalid JSON silently dropped here
              └─► verify + confidence score
                    ├─ score ≥ 0.85 + verified  →  MongoDB processed collection
                    └─ score < 0.85 / unverified →  GridFS (image only) + reviews/
```
