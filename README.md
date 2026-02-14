# SmartDoc Enterprise API

**Production-grade RAG system for document intelligence**

🎥 **[3-Minute Demo Video(upcoming)](YOUR_YOUTUBE_LINK_HERE)**  
💻 **[Frontend Repo](https://github.com/amrgaberM/smartdoc-frontend)**

---

## Engineering Decisions & Tradeoffs

*These architectural choices shaped the system's performance and cost profile.*

### **Why pgvector over Pinecone/Weaviate?**
**Decision:** Use PostgreSQL's pgvector extension instead of managed vector databases

**Tradeoff Analysis:**
| Factor | pgvector (Chosen) | Pinecone |
|--------|-------------------|----------|
| **Latency** | <5ms (in-database) | 50-100ms (network call) |
| **Cost** | $0 (existing infra) | $70+/month |
| **Consistency** | ACID transactions | Eventual consistency |
| **Scalability** | Manual sharding at ~1M vectors | Auto-scaling to billions |

**Why it mattered:** For a document system with <100K vectors, in-database search eliminated network latency and simplified the stack. The ACID guarantee meant document and vector updates stay synchronized. Worth noting: if this scales to millions of users, managed solutions would become necessary.

---

### **Why Sliding Window Chunking?**
**Decision:** Implement 1000-character chunks with 200-character overlap instead of fixed-size splitting

**Impact Measured:**
- Baseline (fixed 1000-char, no overlap): 7/10 accuracy on test set
- Sliding window (1000-char, 200 overlap): **9/10 accuracy** (+28% improvement)
- Tradeoff: 20% more chunks to store and search

**Why it worked:** Questions about concepts spanning paragraph boundaries were answered correctly vs missed with fixed chunking. The 200-char overlap preserved context without excessive duplication.

**Code snippet:**
```python
# Sliding window implementation
for i in range(0, len(text), chunk_size - overlap):
    chunk = text[i:i + chunk_size]
    if len(chunk.strip()) > 50:
        chunks.append(chunk)
```

---

### **Why Lazy-Load Embedding Model?**
**Decision:** Load 400MB Sentence Transformers model on first query, not at startup

**Performance Impact:**
- Cold start (first query): ~30 seconds
- Warm queries (subsequent): ~11 seconds
- Memory saved at startup: 400MB

**Rationale:** Optimized for production where services run 24/7. First-query latency acceptable because:
1. One-time cost per deployment
2. Most users don't query immediately after system restart
3. Saved memory allows more worker processes

**Alternative considered:** Pre-load at startup (rejected due to 8-second startup penalty affecting deployments)

---

### **Why Celery over AWS Lambda?**
**Decision:** Use persistent Celery workers instead of serverless functions

**Comparison:**
| Aspect | Celery (Chosen) | AWS Lambda |
|--------|-----------------|------------|
| **Cold Start** | None (always running) | 2-5 seconds |
| **Model Loading** | Once at startup | Every invocation |
| **Cost (10K docs/month)** | ~$15 (fixed workers) | ~$45 (per-invocation) |
| **Complexity** | Moderate | High (SAM/CDK) |

**Why it fit:** Document analysis is CPU-intensive but predictable. Keeping the 400MB model in memory across requests avoided repeated loading costs. Serverless would reload the model per-document (~8s overhead each time).

---

### **What I'd Do Differently at Scale**

**Current system handles:** <1K users, <100K documents

**At 10K+ users, I'd change:**

1. **Add Redis caching layer**
   - Problem: Repeated questions hit LLM every time
   - Solution: Cache query embeddings + answers for 24 hours
   - Expected impact: 100x speedup for common questions, 60% cost reduction

2. **Implement streaming responses**
   - Problem: 11-second wait for complete answer
   - Solution: Server-Sent Events to stream tokens as generated
   - Expected impact: Perceived latency drops to 2-3 seconds (first tokens)

3. **Switch to managed vector DB**
   - Problem: pgvector requires manual index management
   - Solution: Migrate to Pinecone/Weaviate when crossing 500K vectors
   - Trigger point: When query latency exceeds 200ms consistently

4. **Add automatic chunk size optimization**
   - Problem: 1000-char chunks arbitrary, not optimized per document type
   - Solution: A/B test different sizes, measure accuracy per document category
   - Expected impact: 5-10% accuracy improvement for specific doc types

---

## What This Is

SmartDoc is a semantic search API that lets you ask questions about PDF documents with 9/10 accuracy. Built to demonstrate production RAG architecture patterns.

**Key Challenge Solved:** Processing PDFs 10x faster (3min → 17s) while maintaining high accuracy through custom chunking algorithms and async task processing.

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

## Technical Implementation

### RAG Pipeline
- **Chunking:** Sliding window (1000 characters, 200 character overlap)
- **Embeddings:** 768-dimensional vectors using all-mpnet-base-v2 (SentenceTransformers)
- **Search:** PostgreSQL pgvector extension with cosine similarity
- **Generation:** Llama-3.3-70b via Groq API with custom prompts for citation

### Async Architecture
- **Task Queue:** Celery with Redis as message broker
- **Workers:** 4 worker processes configured in docker-compose
- **Design Pattern:** Non-blocking uploads - API returns immediately while processing happens in background
- **Status Tracking:** Pending → Processing → Completed/Failed states

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

# Access
API: http://localhost:8000/api/
Swagger Docs: http://localhost:8000/api/docs/
```

---

## Tech Stack

**Backend:** Python 3.11, Django 5.2, Django REST Framework  
**Database:** PostgreSQL 16 + pgvector extension  
**Queue:** Redis 7, Celery 5  
**AI/ML:** Sentence Transformers (all-mpnet-base-v2), Groq API (Llama-3.3-70b)  
**Deployment:** Docker + Docker Compose  
**Frontend:** Next.js 14, TypeScript, Tailwind CSS  

---

## Testing
```bash
# Run all tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=documents --cov=users
```

**Test coverage:** ~65% (focus on API endpoints, authentication, serializers)

**Accuracy test set:**
- 10 questions with known correct answers based on 68-page PDF
- Manual verification: 9/10 correct
- Failed case: Question about specific example - system retrieved relevant chunks but LLM interpretation was off

---

## Known Limitations

**By Design:**
- Cold start on first query (expected due to lazy loading)
- No response streaming (full generation before returning)
- No query caching (deliberate - shows real LLM performance)

**Production Gaps:**
- No automated accuracy regression tests
- Single-tenant only (no row-level security for multi-org)
- Failed API calls not automatically retried

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

