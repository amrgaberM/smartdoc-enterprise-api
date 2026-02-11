##  Technical Highlights: The RAG Pipeline

This project implements a full **Retrieval-Augmented Generation (RAG)** architecture:

* **Asynchronous Processing:** Uses **Celery & Redis** to handle heavy PDF text extraction and vectorization in the background.
* **Vector Database:** Leverages **pgvector** (Postgres) to store and query 768-dimensional text embeddings.
* **Semantic Chunking:** Implements a **Sliding Window** algorithm to maintain context across document paragraphs, preventing "context loss" during retrieval.
* **LLM Integration:** Connected to **Llama-3 via Groq API** for ultra-low latency response generation based on retrieved context.
* **Containerized Architecture:** Fully orchestrated with **Docker Compose**, separating the API, Database, Redis, and Worker layers for scalability.