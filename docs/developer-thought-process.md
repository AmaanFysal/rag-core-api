# Developer Thought Process — Building from Scratch

## The Starting Thought

> "I want users to upload documents and ask questions about them using AI."

That one sentence defines everything. Now break it into problems to solve.

---

## Step 1 — What data do I need to store?

The developer thinks:
- I need to store **documents** (filename, who uploaded it, status)
- I need to store **chunks** of those documents (the text + the vector)

So he designs the database models first — `Document` and `Chunk`. Everything else depends on these.

---

## Step 2 — How does a document get in?

> "A user uploads a file. I need to save it, read its text, split it into pieces, and convert each piece into a vector."

This becomes the **upload pipeline**:
```
file upload → save to disk → extract text → chunk → embed → store in DB
```

He builds this step by step — one utility at a time (`text_extraction`, `chunking`, `embeddings`) then wires them together in `ProcessingService`.

---

## Step 3 — How does a question get answered?

> "A user asks a question. I need to find the most relevant chunks, then ask the LLM to answer using those chunks."

This becomes the **RAG pipeline**:
```
question → embed → search DB → build context → LLM → answer
```

He separates the search part (`RetrievalService`) from the answer part (`RAGService`) because search is also useful on its own.

---

## Step 4 — Who is allowed to do what?

> "Users should only see their own documents. I need login."

So he adds:
- Auth route — login, get a token
- JWT — prove who you are on every request
- `owner_id` on every query — so users are isolated

---

## Step 5 — What could go wrong?

> "What if someone uploads a 1GB file? What if they spam the API?"

So he adds:
- Request size limit middleware
- Rate limiting on upload, search, ask

---

## Step 6 — How do I know it's running?

> "I need a simple health check so I can monitor the server."

So he adds `GET /health`.

---

## The Mental Model

A good developer thinks in **layers**:

```
1. What is the data?          → Models (Document, Chunk)
2. How does data get in?      → Upload pipeline (utils + services)
3. How does data get used?    → RAG pipeline (retrieval + LLM)
4. Who can access what?       → Auth + JWT
5. How do I protect it?       → Rate limits + size limits
6. How do I expose it?        → Routes (the API layer, built last)
```

Notice routes are **built last** — they are just the front door. All the real logic lives in services and utils. The route just receives the request, calls a service, and returns the result.

---

## The Key Insight

> Services and utilities do the work. Routes just connect the outside world to that work.

That's why `ask.py` is only 30 lines — it does nothing itself. It just takes the request, passes it to `RAGService`, and returns the result.
