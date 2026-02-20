# SmartDoc API - Demo Deployment

**Live Demo:** [Will be added after deployment]

Deployment-optimized version of SmartDoc RAG system.

## Architecture

**Demo Version:**
- FastAPI (async framework)
- BackgroundTasks (async processing)
- Supabase PostgreSQL + pgvector
- Groq LLM API

**Production Version:** See `main` branch for full Celery + Redis architecture

## Quick Start
```bash
# Clone demo branch
git clone -b demo-deployment https://github.com/amrgaberM/smartdoc-enterprise-api
cd smartdoc-enterprise-api

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your DATABASE_URL and GROQ_API_KEY

# Run locally
uvicorn main:app --reload

# Access
API: http://localhost:8000
Docs: http://localhost:8000/docs
```

## API Endpoints
```
POST   /documents/           Upload PDF
GET    /documents/           List documents
GET    /documents/{id}       Get document details
POST   /documents/{id}/ask   Ask question
DELETE /documents/{id}       Delete document
GET    /health               Health check
```

## Demo vs Production

| Feature | Demo | Production |
|---------|------|------------|
| Framework | FastAPI | Django |
| Async Tasks | BackgroundTasks | Celery + Redis |
| Database | Supabase | Self-hosted PostgreSQL |
| Scaling | Vertical | Horizontal |
| Cost | $0 | ~$15/month |

## Deployment

Deployed on Railway with Supabase PostgreSQL.

**Production architecture:** See `main` branch

## Tech Stack

- FastAPI
- PostgreSQL + pgvector
- Sentence Transformers
- Groq API (Llama-3.3)
- Docker

---

Built to demonstrate RAG architecture patterns.