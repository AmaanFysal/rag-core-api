# RAG Core API

A production-grade Retrieval-Augmented Generation (RAG) backend — built to demonstrate what a real AI system looks like beyond a tutorial. Not a demo, not a Jupyter notebook. An actual deployed service with auth, rate limiting, vector search, and a live frontend.

**Live demo:** [rag-core-api.vercel.app](https://rag-core-api.vercel.app)
**API docs:** [rag-api-production-13c4.up.railway.app/docs](https://rag-api-production-13c4.up.railway.app/docs)
**Repo:** [github.com/AmaanFysal/rag-core-api](https://github.com/AmaanFysal/rag-core-api)

---

## Why I Built This

Most RAG tutorials stop at "upload a PDF, get an answer." That's the easy part. What they skip:

- How do you stop one user from reading another user's documents?
- How do you prevent someone from hammering your OpenAI bill with 1000 requests?
- How do you make the whole thing async so it doesn't block under load?
- How do you ship it so it's actually running somewhere?

This project answers all of that. The goal was to build a system I'd be comfortable putting in front of real users — not a proof of concept.

---

## What It Does

Upload documents. Ask questions. Get answers grounded in the content of those documents, not hallucinated from model weights.

The system:

1. Accepts file uploads (PDF, TXT) and extracts text
2. Splits the text into token-aware chunks
3. Embeds each chunk using OpenAI's `text-embedding-3-small`
4. Stores embeddings in PostgreSQL via `pgvector`
5. On query: embeds the question, finds the closest chunks by cosine distance
6. Assembles those chunks as context and prompts GPT-4o-mini
7. Returns the answer with source citations

Every step is scoped to the authenticated user. User A cannot see User B's documents.

---

## System Architecture

### High-Level Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Browser)                         │
│                    frontend/index.html                          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                          │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  Size Limit      │  │   CORS Middleware │  │ Rate Limiter  │  │
│  │  Middleware      │  │   (all origins)  │  │  (slowapi)    │  │
│  │  10MB upload     │  │                  │  │  2/day ask    │  │
│  │  1MB other       │  │                  │  │  10/min upload│  │
│  └────────┬────────┘  └──────────────────┘  └───────────────┘  │
│           │                                                      │
│  ┌────────▼────────────────────────────────────────────────┐    │
│  │                      Routes                             │    │
│  │  POST /auth/token   GET  /documents/                    │    │
│  │  POST /documents/upload   GET /documents/{id}/content   │    │
│  │  POST /search/      POST /ask/                          │    │
│  └────────┬────────────────────────────────────────────────┘    │
│           │ Depends(get_current_user) — JWT verified here       │
│           ▼                                                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                     Services                           │     │
│  │  DocumentService  ProcessingService  RetrievalService  │     │
│  │                        RagService                      │     │
│  └────────┬───────────────────────────┬───────────────────┘     │
│           │                           │                          │
└───────────┼───────────────────────────┼──────────────────────────┘
            │                           │
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────────────────┐
│  PostgreSQL (Railway) │   │         OpenAI API                │
│  + pgvector           │   │  text-embedding-3-small (1536d)   │
│                       │   │  gpt-4o-mini (generation)         │
│  documents table      │   └───────────────────────────────────┘
│  chunks table         │
│  owner_id indexed     │
└───────────────────────┘
```

---

### Document Ingestion Pipeline

```
POST /documents/upload (multipart/form-data)
          │
          ▼
  ┌───────────────┐
  │ JWT verified  │ ← owner_id from token, never from client
  │ 10MB limit    │
  │ SHA-256 hash  │ ← deduplication: same file = same hash, skip
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │  Create stub  │ status: "uploaded"
  │  Store file   │ → local disk / storage_path
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │ Extract text  │ → pdfplumber (PDF) / plain read (TXT)
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │  Token chunk  │ → tiktoken cl100k_base, ~512 tokens/chunk
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │   Embed each  │ → OpenAI text-embedding-3-small → 1536d float
  │     chunk     │
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │ Store vectors │ → chunks table, Vector(1536) column
  │ Update status │ status: "ready" (or "failed" on error)
  └───────────────┘
```

---

### RAG Query Pipeline

```
POST /ask/  { "query": "...", "document_ids": [1, 2] }
          │
          ▼
  ┌───────────────┐
  │ JWT verified  │ ← owner_id scopes all DB queries
  │ Rate limited  │ ← 2 questions / day / IP
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │  Embed query  │ → text-embedding-3-small → 1536d vector
  └───────┬───────┘
          │
          ▼
  ┌───────────────────────────────────┐
  │  Vector similarity search         │
  │                                   │
  │  SELECT chunks.*                  │
  │  JOIN documents ON owner_id = me  │
  │  WHERE doc_id IN [1, 2]           │  ← optional filter
  │  ORDER BY embedding <=> query_vec │  ← cosine distance
  │  LIMIT top_k                      │
  └───────┬───────────────────────────┘
          │
          ▼
  ┌───────────────┐
  │  Build prompt │ system + retrieved chunks + user question
  └───────┬───────┘
          │
          ▼
  ┌───────────────┐
  │  gpt-4o-mini  │ → grounded answer
  └───────┬───────┘
          │
          ▼
  { "answer": "...", "sources": [chunk_ids] }
```

---

## Security Model

**The core guarantee:** `owner_id` is never trusted from the client. It is derived exclusively from the verified JWT.

```
Client sends:  POST /documents/upload  (no owner_id in body)
                Authorization: Bearer <JWT>
                                    │
                                    ▼
                          decode_access_token()
                          extracts sub claim
                                    │
                                    ▼
                   owner_id = "alice"   ← from token, not client
```

This eliminates a class of IDOR (Insecure Direct Object Reference) bugs where clients can claim another user's identity by sending a different ID in the request body.

**Authentication flow:**

```
POST /auth/token
  username=alice&password=alice_password
          │
          ▼
  bcrypt.checkpw(password, stored_hash)
          │
          ▼
  JWT signed with HS256
  { "sub": "alice", "exp": now + 60min }
          │
          ▼
  { "access_token": "eyJ...", "token_type": "bearer" }
```

All subsequent requests include `Authorization: Bearer <token>`. The JWT is verified on every protected route via FastAPI's dependency injection — no session storage, no database lookup per request.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Framework | FastAPI | Async-first, automatic OpenAPI docs, dependency injection |
| Database | PostgreSQL 17 + pgvector | Native vector operations, no separate vector DB needed |
| ORM | SQLAlchemy 2.0 (async) | Type-safe, asyncpg driver, clean session management |
| Migrations | Alembic | Version-controlled schema changes, auto-generates diffs |
| Auth | python-jose (JWT HS256) | Stateless, no DB lookup per request |
| Passwords | bcrypt | Industry-standard adaptive hashing |
| Rate Limiting | slowapi | Decorator-based, plugs into FastAPI with one line |
| Embeddings | OpenAI text-embedding-3-small | 1536d, cost-effective, state-of-the-art retrieval quality |
| Generation | OpenAI gpt-4o-mini | Fast, cheap, good at instruction-following |
| Chunking | tiktoken (cl100k_base) | Token-aware splitting — no mid-word or mid-sentence cuts |
| Text extraction | pdfplumber | Accurate PDF text extraction including tables |
| Infra | Railway (API + DB) | One-command deploy, managed Postgres with pgvector image |
| Frontend | Vercel (static HTML) | Zero-config deploy, global CDN, Analytics built in |

---

## Project Structure

```
rag-core-api/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py          # POST /auth/token
│   │       ├── document.py      # upload, list, read content
│   │       ├── search.py        # semantic search
│   │       ├── ask.py           # full RAG pipeline
│   │       └── health.py        # GET /health
│   │
│   ├── core/
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   ├── security.py          # JWT create/decode, bcrypt auth
│   │   ├── dependencies.py      # get_current_user dependency
│   │   └── limiter.py           # slowapi Limiter instance
│   │
│   ├── middleware/
│   │   └── size_limit.py        # request body size enforcement
│   │
│   ├── services/
│   │   ├── document_service.py  # document CRUD + deduplication
│   │   ├── processing_service.py # chunk + embed pipeline
│   │   ├── retrieval_service.py  # vector similarity search
│   │   └── rag_service.py        # LLM prompt assembly + call
│   │
│   ├── models/
│   │   ├── document.py          # SQLAlchemy Document model
│   │   └── chunk.py             # SQLAlchemy Chunk + Vector column
│   │
│   ├── schemas/
│   │   ├── auth.py              # TokenResponse
│   │   ├── document.py          # DocumentCreate, DocumentResponse
│   │   ├── search.py            # SearchRequest, SearchResponse
│   │   └── ask.py               # AskRequest, AskResponse
│   │
│   ├── utils/
│   │   ├── embeddings.py        # OpenAI embedding wrapper
│   │   ├── llm.py               # OpenAI completion wrapper
│   │   ├── chunking.py          # tiktoken token chunker
│   │   ├── text_extraction.py   # pdfplumber / plain text
│   │   └── file_storage.py      # disk read/write
│   │
│   ├── db/
│   │   ├── base.py              # SQLAlchemy Base
│   │   └── session.py           # async engine + session factory
│   │
│   └── main.py                  # app factory, middleware, routers
│
├── alembic/
│   ├── versions/                # migration scripts
│   └── env.py                   # reads DATABASE_URL env var
│
├── tests/
│   ├── conftest.py              # AsyncClient, token fixtures
│   ├── test_auth.py             # 7 auth tests
│   └── test_cross_tenant.py     # 5 isolation tests
│
├── frontend/
│   └── index.html               # macOS-style dark UI, no framework
│
├── scripts/
│   └── seed_docs.py             # seeds demo documents via API
│
├── docker-compose.yml           # local pgvector Postgres
├── Procfile                     # Railway: migrate then start
├── requirements.txt
└── .env.example
```

---

## API Reference

All protected endpoints require `Authorization: Bearer <token>`.

### Auth

```
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=alice&password=alice_password

→ { "access_token": "eyJ...", "token_type": "bearer" }
```

### Documents

```
POST   /documents/upload          multipart/form-data, file field
                                  Rate: 10/min
                                  Max: 10 MB

GET    /documents/                → list all docs for current user
GET    /documents/{id}/content    → raw text content of document
```

### Search

```
POST /search/
{ "query": "string", "top_k": 5 }

Rate: 30/min
→ { "results": [ { "chunk_id": 1, "content": "...", "score": 0.87 } ] }
```

### Ask (RAG)

```
POST /ask/
{ "query": "string", "top_k": 5, "document_ids": [1, 2] }

Rate: 2/day
document_ids is optional — omit to search all your documents

→ { "answer": "...", "sources": [2, 1] }
```

---

## Database Schema

### documents

| Column | Type | Notes |
|---|---|---|
| id | serial | Primary key |
| owner_id | varchar | NOT NULL, indexed — from JWT |
| filename | varchar | Original filename |
| file_type | varchar | pdf / txt |
| status | varchar | uploaded / processing / ready / failed |
| content_hash | varchar | SHA-256 — prevents duplicate ingestion |
| storage_path | varchar | Disk path to raw file |
| uploaded_at | timestamp | UTC |
| error_message | text | Set on failed status |

### chunks

| Column | Type | Notes |
|---|---|---|
| id | serial | Primary key |
| document_id | integer | FK → documents(id) |
| chunk_index | integer | Position in document |
| content | text | Raw chunk text |
| embedding | vector(1536) | pgvector column — cosine search |

---

## Design Decisions & Tradeoffs

### What I got right

**Async throughout.**
Every database call uses `AsyncSession` with `asyncpg`. FastAPI handles requests concurrently. No thread blocking, no connection pool exhaustion under load.

**owner_id from JWT, not client.**
The obvious insecure approach is `owner_id: str = Form(...)`. Any client could send any value. By sourcing it from the verified JWT sub claim, cross-tenant access is architecturally impossible at the service layer.

**Token chunking over character chunking.**
Naive character splits cut words in half, break sentences unpredictably, and waste tokens. tiktoken-based splitting respects the model's token budget and produces semantically cleaner chunks that embed and retrieve better.

**SHA-256 deduplication.**
Uploading the same file twice silently returns the existing document instead of embedding the same content again. Saves OpenAI API costs and keeps the vector index clean.

**Single Postgres, no separate vector DB.**
pgvector runs inside Postgres. One database connection, one infrastructure dependency, ACID guarantees across document metadata and embeddings. Weaviate/Pinecone add operational complexity before you have a scaling problem.

**Separate limiter module.**
`slowapi`'s `Limiter` instance must be created before routes import it. Defining it in `main.py` and importing from routes causes a circular import. One dedicated `limiter.py` solves this cleanly.

### What I'd change at scale

**No vector index on chunks.embedding.**
Currently every similarity search is a full table scan with exact cosine distance. This is fine up to ~100k chunks. For production scale, an IVFFlat or HNSW index would drop query time from O(n) to near O(log n).

```sql
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
```

**Synchronous embedding in request handler.**
When a document is uploaded, chunking and embedding happen inline before the response returns. On a 100-page PDF this takes seconds. Better: return a job ID immediately, process in a background task (Celery/ARQ), expose a status endpoint.

**In-memory user store.**
`USERS_SEED` builds a dict at startup from an env variable. Fine for a demo, wrong for a product. A real system needs a `users` table, a registration endpoint, email verification, and password reset.

**No vector index, no hybrid search.**
Pure vector similarity misses exact keyword matches. BM25 + vector (hybrid search) with RRF fusion significantly improves recall. pgvector 0.7+ supports this natively.

**Rate limiting is per-IP, not per-user.**
Shared NAT (office, university) means one IP = many users. Token-based rate limiting scoped to JWT sub would be fairer and more abuse-resistant.

---

## What I'd add next (Roadmap)

- [ ] **Async background ingestion** — job queue + status polling endpoint
- [ ] **HNSW index** on chunk embeddings for sub-millisecond search at scale
- [ ] **Hybrid search** — BM25 + vector with reciprocal rank fusion
- [ ] **User registration + DB-backed auth** — replace USERS_SEED with a proper users table
- [ ] **Streaming answers** — `text/event-stream` SSE for real-time token output
- [ ] **Re-ranking** — Cohere Rerank or cross-encoder to improve top-k relevance
- [ ] **Multi-file format support** — Word (.docx), Markdown, HTML
- [ ] **Chunk overlap** — optional context overlap between adjacent chunks to avoid answer fragmentation
- [ ] **Observability** — structured logging, OpenTelemetry traces, token usage tracking per user
- [ ] **Admin panel** — usage dashboard, user management, document analytics

---

## Running Locally

### Prerequisites

- Python 3.11+
- Docker
- OpenAI API key

### Setup

```bash
git clone https://github.com/AmaanFysal/rag-core-api
cd rag-core-api

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Environment

Create `.env`:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ragdb
OPENAI_API_KEY=sk-...
JWT_SECRET_KEY=<generate below>
JWT_EXPIRY_MINUTES=60
USERS_SEED=alice:alice_password,bob:bob_password
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Database

```bash
docker-compose up -d          # starts pgvector/pgvector:pg17
alembic upgrade head          # runs all migrations
```

### Run

```bash
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

### Running Tests

```bash
pytest tests/ -v
```

12 tests covering: auth (missing/bad/expired/valid token, login, wrong password), cross-tenant isolation (owner_id from JWT, body field ignored, unauthenticated upload).

---

## Deploying to Railway + Vercel

### Backend (Railway)

1. Install Railway CLI: `npm install -g @railway/cli`
2. `railway login && railway init`
3. Add a **PostgreSQL** service using image `pgvector/pgvector:pg17` (not the default Postgres — the default image doesn't include the vector extension)
4. Set environment variables in Railway dashboard:
   ```
   OPENAI_API_KEY=sk-...
   JWT_SECRET_KEY=<generated>
   JWT_EXPIRY_MINUTES=60
   USERS_SEED=alice:password,bob:password
   DATABASE_URL=<Railway provides this automatically>
   ```
5. The `Procfile` handles migrations at startup:
   ```
   web: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
6. `railway up` — Railway builds and deploys

**Critical note on DATABASE_URL:** Railway provides `postgresql://` (psycopg2 scheme). The app's `session.py` rewrites it to `postgresql+asyncpg://` at runtime. The `alembic/env.py` does the inverse (strips `+asyncpg`) for synchronous migration runs.

### Frontend (Vercel)

The frontend is a single static HTML file — no build step.

1. Point Vercel to the repo, set root to `frontend/`
2. No environment variables needed — the API URL is hardcoded in `index.html` (it's public anyway)
3. Deploy

---

## Tests

```
tests/
├── conftest.py
│   ├── client fixture        AsyncClient(app=app)
│   ├── alice_token fixture   valid JWT for alice
│   ├── bob_token fixture     valid JWT for bob
│   └── expired_token fixture JWT with exp in the past
│
├── test_auth.py              (7 tests)
│   ├── missing token → 401
│   ├── garbage token → 401
│   ├── wrong signature → 401
│   ├── expired token → 401
│   ├── valid token → 200
│   ├── login → token
│   └── wrong password → 401
│
└── test_cross_tenant.py      (5 tests)
    ├── search uses JWT owner_id (mocked service, assert call args)
    ├── ask uses JWT owner_id
    ├── upload uses JWT owner_id
    ├── client body owner_id is ignored (schema field removed)
    └── unauthenticated upload → 401
```

---

## Frontend

A single HTML file — no framework, no build pipeline, no npm. macOS-style dark window.

**How it works:**
1. On load, auto-authenticates as `alice` and fetches document list
2. Documents appear as draggable icons in the sidebar
3. Drag icons into the drop zone — they appear as chips
4. Type a question; the ask request sends only the selected document IDs
5. Answer appears in the output box with a clear button
6. Rate limit hit → input locks with "2 questions per day per IP" message

The drag-to-zone pattern was a deliberate UX choice: it makes document selection feel tactile and makes the scoping of the question visible ("I am asking about these specific documents").

---

## What This Demonstrates

If you're reading this as a hiring manager or technical reviewer:

**Backend engineering:** Async FastAPI with proper separation of concerns across routes, services, and utilities. Not everything in one file.

**Security thinking:** IDOR prevention via JWT-scoped identity. Rate limiting. Request size limits. Middleware layering. Multi-tenant isolation at the database query level.

**AI/ML integration:** Embedding pipeline, vector storage, cosine similarity retrieval, context assembly, grounded LLM prompting, source citations.

**Infra:** Railway deployment with managed Postgres, Alembic migrations baked into startup, Vercel static hosting. Not running on localhost and calling it deployed.

**Testing:** Async integration tests with mocked services. Tests that verify security properties, not just happy paths.

**Pragmatism:** Acknowledged the real tradeoffs — what works now vs. what breaks at scale — rather than pretending the system is perfect.

---

## Author

Built by Amaan Fysal.
