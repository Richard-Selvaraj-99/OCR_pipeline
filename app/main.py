"""
main.py – CLI entry point for the Invoice Extractor pipeline.

Usage examples:
    # Process a single invoice
    python main.py path/to/invoice.jpg

    # Process every image in a folder
    python main.py path/to/invoices/

    # Inspect what is already stored in MongoDB
    python main.py --list
"""

import argparse
import os
import sys

from database import list_invalid_files, list_valid_invoices
from pipeline import process_invoice

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def _collect_images(path: str) -> list[str]:
    """Return a list of image paths from a file or directory argument."""
    if os.path.isfile(path):
        return [path]
    if os.path.isdir(path):
        return [
            os.path.join(path, f)
            for f in sorted(os.listdir(path))
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
        ]
    print(f"Error: '{path}' is not a valid file or directory.")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoice Extractor CLI")
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to an invoice image or a directory of images",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print records currently stored in MongoDB and exit",
    )
    args = parser.parse_args()

    if args.list:
        print("=== Valid Invoices (processed collection) ===")
        for doc in list_valid_invoices():
            inv = doc.get("invoice", {})
            print(
                f"  _id={doc['_id']}  file={doc['source_file']}  "
                f"confidence={doc['confidence']}  "
                f"expenses={inv.get('expenses')}  date={inv.get('date')}"
            )

        print("\n=== Invalid Invoice Files (GridFS) ===")
        for item in list_invalid_files():
            print(
                f"  _id={item['_id']}  file={item['filename']}  "
                f"reason='{item['reason']}'  "
                f"confidence={item['confidence']}  "
                f"uploaded={item['upload_date']}"
            )
        return

    if not args.path:
        parser.print_help()
        sys.exit(0)

    images = _collect_images(args.path)
    if not images:
        print(f"No supported image files found in '{args.path}'.")
        sys.exit(1)

    print(f"Found {len(images)} image(s) to process.\n")
    for image_path in images:
        result = process_invoice(image_path)
        print(result)


if __name__ == "__main__":
    main()
