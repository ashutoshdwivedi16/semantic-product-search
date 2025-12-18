# Applied AI Engineer - Take-Home Assessment

## Overview
Build a semantic search API for an eCommerce product catalog using RAG (Retrieval Augmented Generation). This assignment mirrors real work you'll do in this role and tests your ability to build production-quality LLM applications.

## The Challenge
Create a FastAPI service that allows users to search through a product catalog using natural language queries and get AI-generated responses with relevant product recommendations.

Example queries users might ask:
•	"I need a comfortable office chair under $300"
•	"What laptops are good for video editing?"
•	"Show me waterproof hiking boots for women"

## Requirements

### Part 1: Data Ingestion & Vector Storage (Required)
•	Download the product catalog (CSV is attached)
o	Feel free to scrape additional information from lg.com if needed
•	Parse and chunk the product data appropriately
•	Generate embeddings for product descriptions
•	Store embeddings in a vector database of your choice (Pinecone, Weaviate, ChromaDB, etc.)
•	Document your chunking strategy and why you chose it

### Part 2: API Development (Required)
Build a FastAPI application with the following requirement:

Endpoint: POST /search

Request body:
```json
{
  "query": "user's natural language question",
  "max_results": 5
}
```

Response should include:
•	Relevant products retrieved from vector search
•	An AI-generated natural language summary/recommendation
•	Metadata (execution time, number of products searched, etc.)

### Part 3: LLM Integration (Required)
•	Use any LLM API (OpenAI, Anthropic, etc.) to generate conversational responses
•	Implement prompt engineering to format coherent product recommendations
•	Include the retrieved products as context in your LLM prompt
•	Handle cases where no relevant products are found

### Part 4: Production Considerations (Required)
Implement at least 2 of the following:
•	Input validation and error handling
•	Response caching (for identical queries)
•	Request/response logging
•	Basic rate limiting
•	Streaming responses
•	Unit tests for core functionality

## Deliverables
1.	GitHub Repository containing:
o	All source code
o	README.md with setup instructions
o	requirements.txt or equivalent dependency file
o	.env.example showing required environment variables

2.	README.md must include:
o	Setup and installation instructions
o	How to run the application locally
o	API endpoint documentation
o	Your design decisions and trade-offs
o	What you'd improve with more time

## Evaluation Criteria
We'll assess:
•	Code Quality: Clean, readable, well-structured Python code
•	RAG Implementation: Effective chunking, retrieval, and context usage
•	Prompt Engineering: Quality of AI-generated responses
•	Production Readiness: Error handling, logging, documentation

## Constraints & Guidelines

### Do:
•	Use any libraries/frameworks you're comfortable with
•	Use free tiers of vector databases
•	Ask clarifying questions if anything is unclear
•	Focus on working code over perfect code

### Don't:
•	Build a frontend (API only)
•	Copy-paste without understanding (we'll ask you to explain your choices)