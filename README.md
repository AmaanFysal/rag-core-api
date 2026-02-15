# RAG Core API

Production-ready Retrieval-Augmented Generation (RAG) backend service built with FastAPI, PostgreSQL (pgvector), Async SQLAlchemy, Docker, and Alembic.

This service provides document ingestion, vector search, and grounded LLM responses with strict multi-tenant isolation.

---

## Overview

RAG Core API is an async-first backend designed for AI-powered applications that require:

* Secure document ingestion
* Semantic vector search
* Multi-tenant data isolation
* Grounded large language model responses
* Migration-controlled schema evolution
* Dockerized infrastructure

The system is structured as a modular, production-oriented backend rather than a tutorial implementation.

---

## Architecture

High-level request flow:

```
Client
   |
   v
FastAPI Routes
   |
   |-- Document Service (metadata + storage)
   |-- Processing Service (chunking + embeddings)
   |-- Retrieval Service (vector similarity search)
   |-- RAG Service (context assembly + LLM)
   |
   v
PostgreSQL (pgvector)
```

Core principles:

* Separation of concerns
* Async database access
* Deterministic ingestion states
* Strict tenant isolation
* Vector-native search

---

## Technology Stack

* Python 3.14
* FastAPI
* Async SQLAlchemy 2.0
* PostgreSQL 16
* pgvector
* asyncpg
* Alembic
* Docker
* OpenAI API (embeddings + completion)

---

## Key Features

### 1. Multi-Tenant Safety

Each document includes a mandatory `owner_id` field:

```python
owner_id: str  # NOT NULL, indexed
```

All retrieval and RAG queries are filtered by:

```python
Document.owner_id == owner_id
```

This guarantees logical isolation between users and prevents cross-tenant data leakage.

---

### 2. Document Ingestion Pipeline

Upload endpoint:

```
POST /documents/upload
```

Flow:

1. Create document stub
2. Store file to disk
3. Extract text
4. Chunk text
5. Generate embeddings
6. Store vectors in PostgreSQL
7. Update document status

Document lifecycle states:

* uploaded
* processing
* ready
* failed

---

### 3. Vector Search with pgvector

Embedding column:

```python
embedding: Mapped[list[float] | None] = mapped_column(
    Vector(1536),
    nullable=True
)
```

Similarity query (cosine distance):

```python
Chunk.embedding.cosine_distance(query_embedding)
```

This enables:

* Native vector indexing
* Fast semantic similarity search
* Scalable retrieval layer

---

### 4. Retrieval-Augmented Generation

Ask endpoint:

```
POST /ask
```

Pipeline:

1. Embed user query
2. Perform vector similarity search (top-k)
3. Assemble context from matching chunks
4. Send structured prompt to LLM
5. Return grounded response with source references

Response format:

```json
{
  "answer": "...",
  "sources": [2, 1]
}
```

---

## Database Schema

### documents

| Column        | Type      | Notes             |
| ------------- | --------- | ----------------- |
| id            | integer   | Primary key       |
| filename      | varchar   | Required          |
| file_type     | varchar   | Required          |
| uploaded_at   | timestamp | Required          |
| status        | varchar   | Required          |
| content_hash  | varchar   | Optional          |
| storage_path  | varchar   | Optional          |
| error_message | text      | Optional          |
| owner_id      | varchar   | NOT NULL, indexed |

---

### chunks

| Column      | Type         | Notes          |
| ----------- | ------------ | -------------- |
| id          | integer      | Primary key    |
| document_id | integer      | FK → documents |
| chunk_index | integer      | Required       |
| content     | text         | Required       |
| embedding   | vector(1536) | Nullable       |

---

## Async SQLAlchemy Design

All database interactions use `AsyncSession` and `asyncpg`.

Example:

```python
result = await self.db.execute(stmt)
return result.all()
```

Benefits:

* Non-blocking I/O
* High concurrency
* Clean service isolation
* Production-grade DB handling

---

## Alembic Migrations

Schema changes are managed through Alembic.

Create revision:

```bash
alembic revision --autogenerate -m "message"
```

Apply migration:

```bash
alembic upgrade head
```

Used for:

* Adding embedding column
* Adding owner_id column
* Schema evolution without data loss

---

## Docker Setup

PostgreSQL with pgvector:

```yaml
image: pgvector/pgvector:pg16
```

Start database:

```bash
docker-compose up -d
```

This ensures consistent local and production environments.

---

## API Endpoints

### Upload Document

```
POST /documents/upload
```

### Semantic Search

```
POST /search
```

### Ask (Full RAG)

```
POST /ask
```

---

## Project Structure

```
app/
 ├── api/routes/
 │    ├── document.py
 │    ├── search.py
 │    └── ask.py
 │
 ├── services/
 │    ├── document_service.py
 │    ├── processing_service.py
 │    ├── retrieval_service.py
 │    └── rag_service.py
 │
 ├── models/
 ├── schemas/
 ├── db/
 ├── core/
 └── utils/
```

Layered design:

* Routes → HTTP layer
* Services → business logic
* Models → persistence
* Schemas → validation
* Utils → embeddings, LLM, chunking

---

## Running Locally

Activate environment:

```bash
source .venv/bin/activate
```

Start database:

```bash
docker-compose up -d
```

Run API:

```bash
uvicorn app.main:app --reload
```

Open API docs:

```
http://127.0.0.1:8000/docs
```

---

## Production-Ready Characteristics

* Async-first architecture
* Vector-native semantic search
* Multi-tenant isolation
* Explicit ingestion lifecycle
* Dockerized infrastructure
* Migration-controlled schema
* Modular service design
* LLM-grounded responses
