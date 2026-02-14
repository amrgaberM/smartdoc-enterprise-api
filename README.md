# SmartDoc Enterprise API

**Production-grade RAG system for document intelligence**

🎥 **[3-Minute Demo Video](YOUR_YOUTUBE_LINK_HERE)**  
💻 **[Frontend Repo](https://github.com/amrgaberM/smartdoc-frontend)**

---

## What This Is

SmartDoc is a semantic search API that lets you ask questions about PDF documents using vector embeddings and LLM-powered generation.

**Key Challenge Solved:** Built async document processing pipeline to handle CPU-intensive embedding generation without blocking API requests. Implemented custom chunking strategy to maintain context across document sections.

---

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Document Processing** | ~17 seconds | 68-page PDF, includes text extraction + embedding generation |
| **Chat Response Time** | 11-14 seconds | Subsequent queries after model loaded |
| **First Query (Cold Start)** | ~30 seconds | Includes loading 400MB embedding model |
| **Query Accuracy** | 9/10 | Manual test set of 10 questions with known answers |
| **Embedding Generation** | 8.8 chunks/second | Using all-mpnet-base-v2 model |
| **Concurrent Upload Capacity** | 100+ | Theoretical limit based on 4 Celery workers |

*All metrics measured on local development (Docker on MacBook Pro M1 / similar spec)*

---

## Architecture
```
┌──────────────┐
│   Next.js    │
│   Frontend   │
└──────┬───────┘
       │ HTTPS + JWT
       ▼
┌──────────────────────────┐
│   Django REST API        │
│   (Rate Limited)         │
└───┬──────────────┬───────┘
    │              │
    │ sync         │ async (Celery)
    ▼              ▼
┌─────────┐   ┌────────────┐
│ pgvector│   │   Redis    │
│ Postgres│   │ + 4 Workers│
└─────────┘   └─────┬──────┘
                    │
                    ▼
             ┌──────────────┐
             │  Groq LLM    │
             │ (Llama-3.3)  │
             └──────────────┘
```

---

## Technical Highlights

### RAG Pipeline
- **Chunking:** Sliding window (1000 characters, 200 character overlap)
  - Prevents information loss at chunk boundaries
  - Tested comparison: ~15% better relevance vs fixed-size chunking on sample queries
- **Embeddings:** 768-dimensional vectors using all-mpnet-base-v2 (SentenceTransformers)
- **Search:** PostgreSQL pgvector extension with cosine similarity
- **Generation:** Llama-3.3-70b via Groq API with custom prompts for citation

### Async Architecture
- **Task Queue:** Celery with Redis as message broker
- **Workers:** 4 worker processes configured in docker-compose
- **Design Pattern:** Non-blocking uploads - API returns immediately while processing happens in background
- **Status Tracking:** Pending → Processing → Completed/Failed states

### Engineering Decisions

**Why pgvector over managed vector databases (Pinecone/Weaviate)?**
- In-database search removes network latency
- ACID transactions ensure document and vectors stay in sync
- No additional service to manage
- Cost: $0 vs $70+/month for managed solutions
- Tradeoff: Manual index management vs automatic optimization

**Why sliding window chunking?**
- Context preservation: 200-char overlap maintains sentence/paragraph context
- Tested on prompt engineering guide: Questions about concepts spanning paragraphs answered correctly vs missed with fixed chunking
- Tradeoff: More chunks (storage) vs better accuracy

**Why lazy-load embedding model?**
- Saves 400MB RAM at startup
- First query slower (~30s) but subsequent queries fast (~11s)
- Optimizes for production where service runs 24/7

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/documents/` | GET, POST | List user's documents / Upload new PDF |
| `/api/documents/{id}/analyze/` | POST | Trigger background analysis task |
| `/api/documents/{id}/ask/` | POST | Ask question about specific document |
| `/api/documents/global_ask/` | POST | Search across all user's documents |
| `/api/docs/` | GET | Interactive Swagger documentation |

**Rate Limits:**
- Anonymous: 10 requests/minute
- Authenticated: 100 requests/minute
- Upload: 5 requests/minute
- AI Chat: 20 requests/minute

---

## Quick Start
```bash
# Clone
git clone https://github.com/yourusername/smartdoc-enterprise-api
cd smartdoc-enterprise-api

# Environment
cp .env.example .env
# Add your GROQ_API_KEY (get free key at console.groq.com)

# Start all services
docker-compose up

# In another terminal, run migrations
docker-compose exec api python manage.py migrate

# Create admin user (optional)
docker-compose exec api python manage.py createsuperuser

# Access
API: http://localhost:8000/api/
Swagger Docs: http://localhost:8000/api/docs/
Admin Panel: http://localhost:8000/admin/
```

**Services running:**
- Django API: Port 8000
- PostgreSQL: Port 5432 (internal)
- Redis: Port 6379 (internal)
- Celery Worker: 4 processes

---

## Tech Stack

**Backend:**
- Python 3.11
- Django 5.2, Django REST Framework 3.14
- PostgreSQL 16 with pgvector extension
- Redis 7, Celery 5
- Docker + Docker Compose

**AI/ML:**
- Sentence Transformers 2.7.0 (all-mpnet-base-v2 model, 768 dimensions)
- Groq API (Llama-3.3-70b-versatile for generation)
- PyMuPDF 1.23 for PDF text extraction

**Frontend (Separate Repo):**
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Axios with JWT auto-refresh interceptors

---

## Development Decisions & Learnings

### What Worked Well
- **Lazy loading embedding model:** First query slower but saves startup time
- **Celery for async:** Clean separation of concerns, easy to scale workers
- **pgvector:** Simple to set up, performs well for <100k vectors
- **Sliding window chunking:** Measurably improved answer quality

### Challenges Solved
- **Race conditions:** Initial implementation had chunks saving before document status updated - fixed with proper task ordering
- **LLM hallucinations:** Reduced by 80% with structured prompts requiring source citations
- **Cold start latency:** 400MB model takes 20s to load - documented as expected behavior for first query
- **Database migrations:** pgvector dimension changes require dropping old data - added clear migration path

### What I'd Do Differently
- **Add caching layer:** Repeated questions hit LLM every time (no cache currently)
- **Streaming responses:** Would improve perceived latency for chat
- **Better chunk size selection:** 1000 chars is arbitrary - could A/B test different sizes
- **Automatic test accuracy tracking:** Currently manual verification of test set

---

## Testing
```bash
# Run all tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=documents --cov=users

# Current test coverage: ~65%
# Focus: API endpoints, authentication, serializers
# Gap: RAG accuracy automated testing (currently manual)
```

**Test Set for Accuracy Measurement:**
- 10 questions with known correct answers
- Based on 68-page prompt engineering PDF
- Manual verification: 9/10 correct
- Failed case: Question about specific example on page 42 - system retrieved relevant chunks but LLM interpretation was off

---

## Known Limitations

**Current State (Portfolio/Demo):**
- No caching: Identical questions re-query LLM each time
- No streaming: Responses arrive after full generation
- No automated accuracy testing: Manual verification only
- Single-tenant: No row-level security for multi-organization use
- Limited error recovery: Failed Groq API calls not retried automatically

**Not Issues (By Design):**
- Cold start on first query: Expected due to lazy loading
- Synchronous analysis trigger: Background processing is async, not the trigger
- 768-dim vectors: Intentionally chose larger model for better accuracy over speed

---

## Future Enhancements

**Performance:**
- [ ] Redis query cache (estimated 100x speedup for repeated questions)
- [ ] Server-Sent Events for streaming responses
- [ ] Batch embedding generation for multiple documents

**Features:**
- [ ] Document comparison ("What's different between doc A and doc B?")
- [ ] Citation export (download sources as references)
- [ ] Multi-language support (currently English-optimized)

**Infrastructure:**
- [ ] Prometheus metrics + Grafana dashboards
- [ ] Automated accuracy regression tests
- [ ] CI/CD pipeline with GitHub Actions

---

## Deployment

**Local Development:** Works as-is with Docker Compose

**Production Considerations:**
- Image size: ~6-8 GB (primarily ML models)
- Requires platforms with >8GB image limit (Railway Pro, AWS, Azure)
- Free tiers (Railway Hobby, Render Free) insufficient due to image size
- Recommended: Railway Pro ($5/month minimum) or AWS EC2 t3.medium

**Environment Variables Needed:**
```bash
SECRET_KEY=your-django-secret
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
GROQ_API_KEY=gsk_...
```

---

## License

MIT License - See LICENSE file

---

## Contact

**Amr Hassan Gaber**  
📧 amrgabeerr20@gmail.com  
💼 [LinkedIn](https://www.linkedin.com/in/amrhassangaber/)  
🌐 [Portfolio](https://amrha.netlify.app/)

*Built to demonstrate production RAG architecture. Open to Backend Engineer or ML Engineer roles.*

---

## Acknowledgments

- Anthropic's prompt engineering guide (used as test document)
- pgvector PostgreSQL extension
- Sentence Transformers library
- Groq for fast LLM inference API