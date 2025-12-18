import os
import time
import logging
from typing import Tuple

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse

from .schemas import SearchRequest, SearchResponse, Product, SearchMetadata
from .retriever import ProductRetriever, DEFAULT_DATASET_PATH, DEFAULT_CHROMA_DIR
from .cache import TTLCache
from .rate_limiter import RateLimiter
from .llm import generate_summary


def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


setup_logging()
app = FastAPI(title="Semantic Product Search API", version="1.0.0")


# Globals (simple in-memory for this exercise)
retriever = ProductRetriever(dataset_path=DEFAULT_DATASET_PATH, persist_dir=DEFAULT_CHROMA_DIR)
cache = TTLCache(ttl_seconds=float(os.getenv("CACHE_TTL", "60")))
rate_limiter = RateLimiter(max_requests=int(os.getenv("RATE_LIMIT", "60")), window_seconds=60)


@app.on_event("startup")
def on_startup():
    # Ensure we have an index. This may take ~seconds on first run.
    total = retriever.ensure_index(force_rebuild=False)
    logging.info("Vector index ready with %d items", total)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000.0
    logging.info("%s %s -> %d in %.2fms", request.method, request.url.path, response.status_code, duration)
    return response


def enforce_rate_limit(request: Request):
    client = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(client):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")


@app.get("/")
def root():
    return {"status": "ok", "items_indexed": retriever.count()}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest, request: Request, _=Depends(enforce_rate_limit)):
    key = (req.query.strip().lower(), req.max_results)
    cached = cache.get(key)
    start = time.time()
    cache_hit = False

    if cached is not None:
        products = cached["products"]
        summary = cached["summary"]
        cache_hit = True
    else:
        products_raw = retriever.search(req.query, k=req.max_results)
        products = [
            Product(
                sku=p.get("sku"),
                name=p.get("name"),
                category=p.get("category", []) or [],
                uri=p.get("uri"),
                msrp=p.get("msrp"),
                final_price=p.get("final_price"),
                release_date=p.get("release_date"),
                in_stock=p.get("in_stock"),
                description=p.get("description"),
                score=p.get("score"),
            ).dict()
            for p in products_raw
        ]
        summary = generate_summary(products, req.query)
        cache.set(key, {"products": products, "summary": summary})

    duration_ms = (time.time() - start) * 1000.0
    metadata = SearchMetadata(
        execution_time_ms=round(duration_ms, 2),
        cache_hit=cache_hit,
        total_index_size=retriever.count(),
        k=req.max_results,
        results_count=len(products),
    )
    return SearchResponse(products=products, summary=summary, metadata=metadata)


@app.get("/healthz")
def healthz():
    return {"ok": True}
