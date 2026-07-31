# Chorus Agent

A production-grade, multi-channel AI assistant backend. One async Python service that
routes conversations from Slack and WhatsApp through a smart multi-provider LLM layer,
equipped with web search, URL reading, code execution, persistent memory (including
semantic vector search), and a live Next.js dashboard.

## Architecture

```
                     ┌─────────────────────────────────────────────┐
                     │               Channels                      │
                     │   Slack (slack-bolt)    WhatsApp (Meta API) │
                     └───────────────┬─────────────────────────────┘
                                     │
                                     ▼
                     ┌─────────────────────────────────────────────┐
                     │          FastAPI + WebSockets (API)         │
                     └───────────────┬─────────────────────────────┘
                                     │
                     ┌───────────────▼─────────────────────────────┐
                     │               Agent Core                    │
                     │  personality ─ tool loop ─ streaming        │
                     └──────┬───────────────────────────┬──────────┘
                            │                           │
              ┌─────────────▼──────────┐   ┌────────────▼────────────┐
              │      Model Router     │   │        Tools            │
              │  smart strategy +     │   │  Serper, Exa, read_url, │
              │  per-provider fallback│   │  code_executor, ...     │
              │  OpenAI/Anthropic/    │   └────────────┬────────────┘
              │  OpenRouter/Bedrock/  │                │
              │  Gemini               │                │
              └─────────────┬─────────┘                │
                            │                          │
              ┌─────────────▼──────────────────────────▼────────────┐
              │                    Memory                          │
              │  PostgreSQL + pgvector (embeddings + cosine search) │
              │  Redis (cache / pub-sub)                           │
              └─────────────────────────────────────────────────────┘
```

## Stack

- **API:** FastAPI + Uvicorn (async), WebSockets for streaming responses
- **Database:** PostgreSQL + pgvector (semantic memory), SQLAlchemy 2 async + asyncpg
- **Cache:** Redis
- **LLM routing:** OpenAI, Anthropic, OpenRouter, AWS Bedrock, Google Gemini with
  `smart` strategy (complex queries → Claude first) and automatic provider fallback
- **Channels:** Slack (slack-bolt), WhatsApp (Meta Cloud API)
- **Tools:** Serper (Google search), Exa (semantic search), URL reader, code executor
- **Dashboard:** Next.js (in `dashboard/`)
- **Quality:** strict mypy, Ruff, pytest

## Setup

### 1. Prerequisites

- Python 3.11+
- Docker (for PostgreSQL + pgvector and Redis)
- Node.js 18+ (dashboard only)

### 2. Infrastructure

```bash
docker compose up -d
```

### 3. Backend

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

cp .env.example .env         # fill in your API keys
uvicorn app:app --reload     # or the entrypoint used in your setup
```

### 4. Dashboard (optional)

```bash
cd dashboard
npm install
npm run dev                  # serves on http://localhost:3000
```

## Configuration

Copy `.env.example` to `.env` and set the keys for the providers/channels you use.
Routing is controlled by:

| Variable           | Purpose                                                        |
| ------------------ | -------------------------------------------------------------- |
| `ROUTING_STRATEGY` | `smart` (default) or provider selection by query complexity     |
| `DEFAULT_PROVIDER` | Fallback provider when the strategy does not apply              |
| `EMBEDDING_MODEL`  | OpenAI embedding model used for semantic memory (`text-embedding-3-small`) |

## Project layout

```
agent/       Agent core: config, personality, orchestration
api/         FastAPI routes and WebSocket streaming
channels/    Slack and WhatsApp integrations
memory/      SQL + vector memory (pgvector cosine search)
models/      Provider clients and the model router
tools/       Agent tools (search, URL reading, code execution)
dashboard/   Next.js admin/chat dashboard
tests/       pytest suite
```

## Development

```bash
ruff check .
mypy .
pytest
```

The vector-memory integration test is skipped unless a reachable database is
provided (requires `OPENAI_API_KEY` and `TEST_DATABASE_URL`):

```bash
set TEST_DATABASE_URL=postgresql+asyncpg://chorus:chorus@localhost:5432/chorus
pytest tests/test_vector_memory_integration.py
```

## Roadmap

- Local embedding model (Ollama) to avoid API cost per memory write
- Headless browser tooling for JS-rendered pages
- Client intake / research agent workflows
