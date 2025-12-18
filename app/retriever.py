import os
import csv
import json
import logging
from typing import List, Dict, Any, Tuple

import chromadb
from chromadb.utils import embedding_functions


DEFAULT_DATASET_PATH = os.getenv("DATASET_PATH", "take_home_dataset.csv")
DEFAULT_CHROMA_DIR = os.getenv("CHROMA_DIR", "vectorstore")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "products")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def _safe_json_loads(value: str, default):
    try:
        return json.loads(value)
    except Exception:
        return default


def _coerce_bool(v: str) -> bool:
    return str(v).strip().upper() in {"Y", "YES", "TRUE", "1"}


def _prepare_product_record(row: Dict[str, str]) -> Tuple[str, str, Dict[str, Any]]:
    """Prepare a single product into Chroma-friendly (id, document, metadata)."""
    sku = row.get("sku") or row.get("id") or ""
    name = row.get("name", "").strip()
    description = (row.get("description") or "").strip()
    categories = _safe_json_loads(row.get("category") or "[]", [])
    bullets_raw = _safe_json_loads(row.get("bullet_features") or "[]", [])
    bullet_points = []
    try:
        for b in bullets_raw:
            if isinstance(b, dict) and "bullet_feature" in b:
                bullet_points.append(b.get("bullet_feature"))
            elif isinstance(b, str):
                bullet_points.append(b)
    except Exception:
        pass

    doc_text = f"{name}\n\n{description}\n\nFeatures: " + "; ".join(bullet_points)

    metadata: Dict[str, Any] = {
        "sku": sku,
        "name": name,
        "category": categories,
        "uri": row.get("uri"),
        "msrp": _try_float(row.get("msrp")),
        "final_price": _try_float(row.get("final_price")),
        "release_date": row.get("release_date"),
        "in_stock": _coerce_bool(row.get("in_stock", "")),
        "description": description,
    }
    return sku, doc_text, metadata


def _try_float(v: Any):
    try:
        return float(v)
    except Exception:
        return None


class ProductRetriever:
    def __init__(self, dataset_path: str = DEFAULT_DATASET_PATH, persist_dir: str = DEFAULT_CHROMA_DIR):
        self.dataset_path = dataset_path
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def _load_dataset(self) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        with open(self.dataset_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    def ensure_index(self, force_rebuild: bool = False) -> int:
        """Create or refresh index from CSV. Returns total count of items in index."""
        existing_count = self.collection.count()
        if not force_rebuild and existing_count > 0:
            return existing_count

        logging.info("Building vector index from dataset: %s", self.dataset_path)
        rows = self._load_dataset()
        ids: List[str] = []
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []
        for row in rows:
            sku, doc_text, metadata = _prepare_product_record(row)
            if not sku:
                continue
            ids.append(sku)
            docs.append(doc_text)
            metas.append(metadata)

        # Reset collection for a fresh build if force
        if force_rebuild:
            try:
                self.client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME, embedding_function=self.embedding_fn
            )

        # Upsert in manageable batches
        BATCH = 500
        for i in range(0, len(ids), BATCH):
            self.collection.upsert(
                ids=ids[i : i + BATCH],
                documents=docs[i : i + BATCH],
                metadatas=metas[i : i + BATCH],
            )

        total = self.collection.count()
        logging.info("Index build complete. Total items: %d", total)
        return total

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        res = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["metadatas", "distances"],
        )
        metadatas = (res.get("metadatas") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]
        products: List[Dict[str, Any]] = []
        for meta, dist in zip(metadatas, distances):
            # Convert distance to a similarity-ish score in [0,1]
            try:
                score = 1.0 / (1.0 + float(dist))
            except Exception:
                score = None
            p = dict(meta)
            p["score"] = score
            products.append(p)
        return products

    def count(self) -> int:
        return self.collection.count()
