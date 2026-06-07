# Open Notebook - Root CLAUDE.md

This file provides architectural guidance for contributors working on Open Notebook at the project level.

## Project Overview

**Open Notebook** is an open-source, privacy-focused alternative to Google's Notebook LM. It's an AI-powered research assistant enabling users to upload multi-modal content (PDFs, audio, video, web pages), generate intelligent notes, search semantically, chat with AI models, and produce professional podcasts—all with complete control over data and choice of AI providers.

**Key Values**: Privacy-first, multi-provider AI support, fully self-hosted option, open-source transparency.

---

## EduNote Fork — Exam-Prep Layer (READ FIRST)

This repo is the **EduNote AI** fork: Open Notebook plus an exam-oriented study layer for a
classroom demo. Most active work happens in the EduNote modules, not upstream code.

**6 EduNote modules** — backend in `api/edunote/`, frontend in `frontend/src/components/edunote/`,
domain model in `open_notebook/domain/edunote.py`:
QuickPrep (`quickprep.py`), ExamAnalyzer (`exam.py`), Quiz (`quiz.py`), Flashcards
(`flashcards.py`), Feynman (uses upstream chat system + `FeynmanChat.tsx`), Progress (`progress.py`).
EduNote tables: `study_session`, `quiz_attempt`, `answer_record`, `flashcard`,
`flashcard_review`, `exam_topic`, `exam_paper`.

### EduNote gotchas (each cost a debugging session)

- **LLM is Groq, not the multi-provider stack.** `llama-3.1-8b-instant` for generation,
  `llama-3.3-70b-versatile` for chat. `GROQ_API_KEY` lives in `.env` — **NEVER commit it.**
  `groq_service.py` lazy-inits so a missing key doesn't crash API import.
- **Groq free-tier rate limits are per-ORG (shared across all demo users), and TPM (tokens
  per minute) is the real concurrency bottleneck — not context size.** Measured TPM:
  `llama-4-scout-17b-16e-instruct` = 30000 (best, use this for chat), `llama-3.3-70b-versatile`
  = 12000 (TPD only 100k — exhausts in a day), `llama-3.1-8b-instant` = 6000 (trap: the smaller
  model has the *smallest* TPM). The demo chat/Feynman model is set via the DB record
  `open_notebook:default_models.default_chat_model` (a DB setting, not code — re-set if DB is wiped).
- **Feynman context is capped to keep requests cheap.** Each full-source context made requests
  ~10k tokens → Groq 413 → HTTP 500. `FeynmanChat.tsx` `trimContext()` caps combined source text to
  `FEYNMAN_CONTEXT_CHAR_BUDGET` (1500 chars) and drops insights. Chinese is ~1 token/char.
- **Standalone JS chunk names are stable (not content-hashed).** After a frontend rebuild, browsers
  that loaded the old build serve cached stale JS; fresh visitors get the new build fine. Hard-reload
  / new profile to verify changes locally.
- **Generation must read BOTH notes and sources.** Uploaded files become `source` records
  (`reference` relation), not `note` records (`artifact` relation). Quiz/flashcard generation uses
  `api/edunote/content.py::gather_notebook_text()` which reads both — otherwise uploaded lectures
  are invisible and QuickPrep reports "no notes found".
- **EduNote FK fields are `string`, not `record<>`.** `flashcard_review.user_id` and
  `study_session.note_id` are plain strings (per-user IDs from `localStorage:edunote:student_id`).
  Migration 17 fixed this; stat queries resolve child rows by `... IN $ids`, not string-FK traversal.
- **`Notebook.delete()` cascades EduNote content** via `_delete_edunote_content()` (8 tables) —
  needed because EduNote rows would otherwise orphan.
- **AI-returns-non-list → return 502** ("AI returned invalid format"), not a bare 500.
- **OCR is not available in the container** (no docling/tesseract). Only text-layer sources work
  (text PDFs, pasted text, URLs, YouTube captions). Scanned PDFs must be OCR'd on the host first.
- **Feynman persona**: the prompt alone leaks citations like `[source:abc]`; `stripCitations()`
  post-processes the displayed text to remove them (reliable, doesn't fight the model).

### Running EduNote things

- **Tests run inside the container** (pytest is a dev dep, not in the prod image):
  `docker-compose exec -T open_notebook sh -c 'cd /app && uv run --no-sync --with pytest --with pytest-asyncio pytest tests/...'`.
  `docker-compose` has a hyphen here. Frontend unit tests: `npx vitest run` in `frontend/`.
- **Frontend is standalone Next.js.** After `npm run build` you must
  `cp -r public .next/standalone/` and `cp -r .next/static .next/standalone/.next/`, then restart
  `PORT=3000 node .next/standalone/server.js` — otherwise logo/static chunks 404.
- **Ports**: frontend 3000, API 5055, SurrealDB 8000 (rocksdb).
- **Demo deploy**: `cloudflared tunnel --url http://localhost:3000` (URL changes each restart).

---

## Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React/Next.js)                    │
│              frontend/ @ port 3000                       │
├─────────────────────────────────────────────────────────┤
│ - Notebooks, sources, notes, chat, podcasts, search UI  │
│ - Zustand state management, TanStack Query (React Query)│
│ - Shadcn/ui component library with Tailwind CSS         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP REST
┌────────────────────────▼────────────────────────────────┐
│              API (FastAPI)                              │
│              api/ @ port 5055                           │
├─────────────────────────────────────────────────────────┤
│ - REST endpoints for notebooks, sources, notes, chat    │
│ - LangGraph workflow orchestration                      │
│ - Job queue for async operations (podcasts)             │
│ - Multi-provider AI provisioning via Esperanto          │
└────────────────────────┬────────────────────────────────┘
                         │ SurrealQL
┌────────────────────────▼────────────────────────────────┐
│         Database (SurrealDB)                            │
│         Graph database @ port 8000                      │
├─────────────────────────────────────────────────────────┤
│ - Records: Notebook, Source, Note, ChatSession, Credential│
│ - Relationships: source-to-notebook, note-to-source     │
│ - Vector embeddings for semantic search                 │
└─────────────────────────────────────────────────────────┘
```

---

## Useful sources

User documentation is at @docs/

## Tech Stack

### Frontend (`frontend/`)
- **Framework**: Next.js 16 (React 19)
- **Language**: TypeScript
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Styling**: Tailwind CSS + Shadcn/ui
- **Build Tool**: Webpack (via Next.js)
- **i18n compatible**: All front-end changes must also consider the translation keys

### API Backend (`api/` + `open_notebook/`)
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **Workflows**: LangGraph state machines
- **Database**: SurrealDB async driver
- **AI Providers**: Esperanto library (8+ providers: OpenAI, Anthropic, Google, Groq, Ollama, Mistral, DeepSeek, xAI)
- **Job Queue**: Surreal-Commands for async jobs (podcasts)
- **Logging**: Loguru
- **Validation**: Pydantic v2
- **Testing**: Pytest

### Database
- **SurrealDB**: Graph database with built-in embedding storage and vector search
- **Schema Migrations**: Automatic on API startup via AsyncMigrationManager

### Additional Services
- **Content Processing**: content-core library (file/URL extraction)
- **Prompts**: AI-Prompter with Jinja2 templating
- **Podcast Generation**: podcast-creator library
- **Embeddings**: Multi-provider via Esperanto

---

## Architecture Highlights

### 1. Async-First Design
- All database queries, graph invocations, and API calls are async (await)
- SurrealDB async driver with connection pooling
- FastAPI handles concurrent requests efficiently

### 2. LangGraph Workflows
- **source.py**: Content ingestion (extract → embed → save)
- **chat.py**: Conversational agent with message history
- **ask.py**: Search + synthesis (retrieve relevant sources → LLM)
- **transformation.py**: Custom transformations on sources
- All use `provision_langchain_model()` for smart model selection

### 3. Multi-Provider AI
- **Esperanto library**: Unified interface to 8+ AI providers
- **Credential system**: Individual encrypted credential records per provider; models link to credentials for direct config
- **ModelManager**: Factory pattern with fallback logic; uses credential config when available, env vars as fallback
- **Smart selection**: Detects large contexts, prefers long-context models
- **Override support**: Per-request model configuration

### 4. Database Schema
- **Automatic migrations**: AsyncMigrationManager runs on API startup
- **SurrealDB graph model**: Records with relationships and embeddings
- **Vector search**: Built-in semantic search across all content
- **Transactions**: Repo functions handle ACID operations

### 5. Authentication
- **Current**: Simple password middleware (insecure, dev-only)
- **Production**: Replace with OAuth/JWT (see CONFIGURATION.md)

---

## Important Quirks & Gotchas

### API Startup
- **Migrations run automatically** on startup; check logs for errors
- **Must start API before UI**: UI depends on API for all data
- **SurrealDB must be running**: API fails without database connection

### Frontend-Backend Communication
- **Base API URL**: Configured in `.env.local` (default: http://localhost:5055)
- **CORS enabled**: Configured in `api/main.py` (allow all origins in dev)
- **Rate limiting**: Not built-in; add at proxy layer for production

### LangGraph Workflows
- **Blocking operations**: Chat/podcast workflows may take minutes; no timeout
- **State persistence**: Uses SQLite checkpoint storage in `/data/sqlite-db/`
- **Model fallback**: If primary model fails, falls back to cheaper/smaller model

### Podcast Generation
- **Async job queue**: `podcast_service.py` submits jobs but doesn't wait
- **Track status**: Use `/commands/{command_id}` endpoint to poll status
- **TTS failures**: Fall back to silent audio if speech synthesis fails

### Content Processing
- **File extraction**: Uses content-core library; supports 50+ file types
- **URL handling**: Extracts text + metadata from web pages
- **Large files**: Content processing is sync; may block API briefly

---

## Component References

See dedicated CLAUDE.md files for detailed guidance:

- **[frontend/CLAUDE.md](frontend/CLAUDE.md)**: React/Next.js architecture, state management, API integration
- **[api/CLAUDE.md](api/CLAUDE.md)**: FastAPI structure, service pattern, endpoint development
- **[open_notebook/CLAUDE.md](open_notebook/CLAUDE.md)**: Backend core, domain models, LangGraph workflows, AI provisioning
- **[open_notebook/domain/CLAUDE.md](open_notebook/domain/CLAUDE.md)**: Data models, repository pattern, search functions
- **[open_notebook/ai/CLAUDE.md](open_notebook/ai/CLAUDE.md)**: ModelManager, AI provider integration, Esperanto usage
- **[open_notebook/graphs/CLAUDE.md](open_notebook/graphs/CLAUDE.md)**: LangGraph workflow design, state machines
- **[open_notebook/database/CLAUDE.md](open_notebook/database/CLAUDE.md)**: SurrealDB operations, migrations, async patterns

---

## Documentation Map

- **[README.md](README.md)**: Project overview, features, quick start
- **[docs/index.md](docs/index.md)**: Complete user & deployment documentation
- **[CONFIGURATION.md](CONFIGURATION.md)**: Environment variables, model configuration
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Contribution guidelines
- **[MAINTAINER_GUIDE.md](MAINTAINER_GUIDE.md)**: Release & maintenance procedures

---

## Testing Strategy

- **Unit tests**: `tests/test_domain.py`, `test_models_api.py`
- **Graph tests**: `tests/test_graphs.py` (workflow integration)
- **Utils tests**: `tests/test_utils.py`, `tests/test_chunking.py`, `tests/test_embedding.py`
- **Run all**: `uv run pytest tests/`
- **Coverage**: Check with `pytest --cov`

---

## Common Tasks

### Add a New API Endpoint
1. Create router in `api/routers/feature.py`
2. Create service in `api/feature_service.py`
3. Define schemas in `api/models.py`
4. Register router in `api/main.py`
5. Test via http://localhost:5055/docs

### Add a New LangGraph Workflow
1. Create `open_notebook/graphs/workflow_name.py`
2. Define StateDict and node functions
3. Build graph with `.add_node()` / `.add_edge()`
4. Invoke in service: `graph.ainvoke({"input": ...}, config={"..."})`
5. Test with sample data in `tests/`

### Add Database Migration
1. Create `migrations/XXX_description.surql`
2. Write SurrealQL schema changes
3. Create `migrations/XXX_description_down.surql` (optional rollback)
4. API auto-detects on startup; migration runs if newer than recorded version

### Deploy to Production
1. Review [CONFIGURATION.md](CONFIGURATION.md) for security settings
2. Use `make docker-release` for multi-platform image
3. Push to Docker Hub / GitHub Container Registry
4. Deploy `docker compose --profile multi up`
5. Verify migrations via API logs

---

## Support & Community

- **Documentation**: https://open-notebook.ai
- **Discord**: https://discord.gg/37XJPXfz2w
- **Issues**: https://github.com/lfnovo/open-notebook/issues
- **License**: MIT (see LICENSE)

