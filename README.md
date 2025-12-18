# Semantic Search API

A semantic search API for eCommerce product catalog using RAG (Retrieval Augmented Generation). This FastAPI service allows users to search through a product catalog using natural language queries and get AI-generated responses with relevant product recommendations.

## Tech Stack
- **FastAPI** for the API server
- **Embeddings**: Sentence-Transformers model `all-MiniLM-L6-v2`
- **Vector DB**: ChromaDB (local persistent store)
- **LLM**: OpenAI Chat Completions (configurable). If no API key is provided, the app gracefully falls back to a deterministic summarizer.
- **Production features**: Input validation, structured logging middleware, basic in-memory rate limiting, response caching (TTL)

## Project Structure
```
- app/
  - main.py: FastAPI app and endpoints
  - schemas.py: Pydantic request/response models
  - retriever.py: Dataset parsing, embedding, ChromaDB storage, vector search
  - llm.py: LLM integration with OpenAI and fallback
  - cache.py: Simple TTL cache for identical queries
  - rate_limiter.py: In-memory sliding-window rate limiter
- scripts/
  - build_index.py: One-off script to (re)build the vector index from CSV
- take_home_dataset.csv: Provided catalog
- .env.example: Environment configuration template
- requirements.txt: Dependencies
```

## Setup and Installation

### Prerequisites
- Python 3.10+ recommended

### Installation Steps

1. **Create a virtual environment and install dependencies**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Optional: put your OpenAI key if you want AI-generated summaries
export OPENAI_API_KEY=sk-...
```

3. **Build the vector index** (first run may take a minute to download the embedding model)
```bash
python scripts/build_index.py
# or force rebuild
python scripts/build_index.py --force
```

### Environment Variables
See `.env.example` for all options. Key ones:
- `DATASET_PATH`: path to the CSV (defaults to `take_home_dataset.csv`)
- `CHROMA_DIR`: where to persist the vector index (defaults to `vectorstore`)
- `EMBEDDING_MODEL`: `all-MiniLM-L6-v2` by default
- `OPENAI_API_KEY`: set to enable AI-generated summaries (optional)
- `OPENAI_MODEL`: defaults to `gpt-4o-mini`
- `LOG_LEVEL`, `CACHE_TTL`, `RATE_LIMIT`: tunables for logging, caching, and rate limiting

## How to Run the Application Locally

1. **Start the API server**
```bash
uvicorn app.main:app --reload --port 8000
```

2. **Try it (HTTP)**
```bash
POST http://localhost:8000/search
Content-Type: application/json

{
  "query": "I need a 34 inch ultrawide monitor for productivity",
  "max_results": 5
}
```

## API Endpoint Documentation

### POST /search
Performs semantic search on the product catalog and returns AI-generated recommendations.

**Request body:**
- `query` (string, required): natural-language question
- `max_results` (int, optional, default 5, range 1-10): number of products to return

**Response body:**
```json
{
  "products": [
    {
      "sku": "34WP65G-B",
      "name": "34 Inch UltraWide FHD HDR FreeSync Monitor",
      "description": "...",
      "features": ["..."],
      "price": 399.99,
      "similarity_score": 0.85
    }
  ],
  "summary": "For productivity, consider LG 34WP65G-B ...",
  "metadata": {
    "execution_time_ms": 123.45,
    "cache_hit": false,
    "total_index_size": 300,
    "k": 5,
    "results_count": 5
  }
}
```

**Fields:**
- `products`: top-k retrieved products with basic fields and similarity scores
- `summary`: AI-generated (or fallback) recommendation
- `metadata`: execution time, cache status, index size, and retrieval parameters

## Design Decisions and Trade-offs

### Chunking Strategy
Each product (name + description + bullet features) is treated as one chunk because catalog entries are short/medium length. This preserves product-level semantics and simplifies retrieval. For much longer product pages, we'd chunk by ~200–300 tokens with slight overlap to maintain context across bullet lists and descriptions.

### Vector Database
ChromaDB was chosen for zero-ops local persistence and easy Sentence-Transformers integration. It stores the index in `./vectorstore` by default.

### Embeddings Model
`all-MiniLM-L6-v2` balances speed and quality and is small enough to download quickly during setup.

### LLM Integration
OpenAI is optional. If `OPENAI_API_KEY` is set, the app uses `gpt-4o-mini` by default; otherwise, a deterministic summary ensures the endpoint always works offline.

### Production Features
Implemented:
- Input validation (Pydantic)
- Structured request logging middleware
- Basic in-memory rate limiting (per-client sliding window)
- TTL response caching for identical queries

## What I'd Improve With More Time

- **Testing**: Add unit tests for ingestion, retrieval, and API responses; CI workflow
- **Caching**: Add persistent caching layer (e.g., Redis) and distributed rate limiting
- **Streaming**: Add streaming responses for the LLM summary
- **Search Enhancement**: Support hybrid search (keyword + vector) and filters (e.g., price < $X, in_stock)
- **Prompt Engineering**: Extend schema and prompt to highlight trade-offs more explicitly (price vs. features)
