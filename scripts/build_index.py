#!/usr/bin/env python3
"""Build or rebuild the local ChromaDB vector index from the CSV dataset.

Usage:
  python scripts/build_index.py [--force]

Environment (optional):
  DATASET_PATH   Path to CSV (default: take_home_dataset.csv)
  CHROMA_DIR     Persist directory for Chroma (default: ./vectorstore)
  EMBEDDING_MODEL SentenceTransformer model name (default: all-MiniLM-L6-v2)
"""

import argparse
import logging

from app.retriever import ProductRetriever


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force rebuild the index")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    r = ProductRetriever()
    total = r.ensure_index(force_rebuild=args.force)
    logging.info("Index items: %d", total)


if __name__ == "__main__":
    main()
