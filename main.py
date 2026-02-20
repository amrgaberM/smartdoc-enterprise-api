from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
from pathlib import Path
import logging

from database import get_db, engine
from models import Base, Document, DocumentChunk
from background import process_document
from embeddings import get_embedding
from llm_utils import generate_answer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="SmartDoc API",
    description="RAG Document Intelligence System - Demo Version",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "SmartDoc API - Demo Version",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/documents/", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Upload a PDF document for processing"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    # Save file
    file_path = UPLOAD_DIR / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"Failed to save file: {str(e)}")
    
    # Create document record
    doc = Document(
        title=file.filename,
        file_path=str(file_path),
        status="pending"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Queue background processing
    background_tasks.add_task(process_document, doc.id)
    
    logger.info(f"Document {doc.id} uploaded and queued")
    
    return {
        "id": doc.id,
        "title": doc.title,
        "status": "processing",
        "message": "Document uploaded. Processing in background."
    }


@app.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Get document details and status"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc:
        raise HTTPException(404, "Document not found")
    
    chunk_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == doc_id
    ).count()
    
    return {
        "id": doc.id,
        "title": doc.title,
        "status": doc.status,
        "analysis_result": doc.analysis_result,
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        "chunk_count": chunk_count
    }


@app.get("/documents/")
def list_documents(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List all documents"""
    docs = db.query(Document).offset(skip).limit(limit).all()
    total = db.query(Document).count()
    
    return {
        "total": total,
        "documents": [
            {
                "id": d.id,
                "title": d.title,
                "status": d.status,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None
            }
            for d in docs
        ]
    }


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Delete a document"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc:
        raise HTTPException(404, "Document not found")
    
    # Delete file
    try:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        logger.warning(f"Failed to delete file: {str(e)}")
    
    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted"}


@app.post("/documents/{doc_id}/ask")
def ask_question(doc_id: int, question: dict, db: Session = Depends(get_db)):
    """Ask a question about a document"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc:
        raise HTTPException(404, "Document not found")
    
    if doc.status != "completed":
        raise HTTPException(400, f"Document not ready. Status: {doc.status}")
    
    q_text = question.get("question", "").strip()
    if not q_text:
        raise HTTPException(400, "Question required")
    
    if len(q_text) > 500:
        raise HTTPException(400, "Question too long (max 500 chars)")
    
    # Generate query embedding
    try:
        query_vector = get_embedding(q_text)
    except Exception as e:
        raise HTTPException(500, f"Embedding failed: {str(e)}")
    
    # Vector search - top 3 chunks
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == doc_id
    ).order_by(
        DocumentChunk.embedding.cosine_distance(query_vector)
    ).limit(3).all()
    
    if not chunks:
        return {
            "answer": "No relevant content found.",
            "sources": [],
            "confidence": "none"
        }
    
    # Generate answer
    try:
        answer = generate_answer(q_text, chunks)
    except Exception as e:
        raise HTTPException(500, f"Answer generation failed: {str(e)}")
    
    sources = [
        {
            "page": c.chunk_index + 1,
            "text": c.text_content[:200] + "..."
        }
        for c in chunks
    ]
    
    return {
        "answer": answer,
        "sources": sources,
        "confidence": "high"
    }


@app.get("/health")
def health_check():
    """Health check"""
    return {"status": "healthy"}