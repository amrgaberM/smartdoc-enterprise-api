import fitz  # PyMuPDF
from database import SessionLocal
from models import Document, DocumentChunk
from embeddings import get_embedding
from llm_utils import generate_beneficial_analysis


def process_document(document_id: int):
    """Background task to process uploaded PDF"""
    db = SessionLocal()
    
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return
        
        doc.status = "processing"
        db.commit()
        
        # Extract text from PDF
        pdf = fitz.open(doc.file_path)
        full_text = ""
        for page in pdf:
            full_text += page.get_text() + "\n"
        full_text = full_text.strip()
        
        if not full_text:
            doc.status = "failed"
            doc.analysis_result = {"error": "No text extracted"}
            db.commit()
            return
        
        # Sliding window chunking
        chunk_size = 1000
        overlap = 200
        chunks = []
        
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk = full_text[i:i + chunk_size]
            if len(chunk.strip()) > 50:
                chunks.append(chunk)
        
        # Generate embeddings and save chunks
        for index, chunk_text in enumerate(chunks):
            vector = get_embedding(chunk_text)
            if vector:
                chunk_obj = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=index,
                    text_content=chunk_text,
                    embedding=vector
                )
                db.add(chunk_obj)
        
        db.commit()
        
        # Generate summary
        insights = generate_beneficial_analysis(full_text[:15000])
        
        # Update document
        doc.status = "completed"
        doc.analysis_result = {
            "insights": insights,
            "summary": insights,
            "page_count": len(pdf),
            "word_count": len(full_text.split()),
            "chunk_count": len(chunks)
        }
        db.commit()
        
    except Exception as e:
        if doc:
            doc.status = "failed"
            doc.analysis_result = {"error": str(e)}
            db.commit()
    finally:
        db.close()