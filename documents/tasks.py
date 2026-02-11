import fitz  # PyMuPDF
from celery import shared_task
from .models import Document, DocumentChunk
from .embeddings import get_embedding

@shared_task
def analyze_document_task(document_id):
    try:
        # Fetch the document
        document = Document.objects.get(id=document_id)
        document.status = 'processing'
        document.save()

        # 1. Extract Text from PDF
        doc = fitz.open(document.file.path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        
        full_text = full_text.strip()
        if not full_text:
            raise ValueError("No text could be extracted from this PDF.")

        # 2. Clear old chunks (in case we are re-analyzing an existing file)
        document.chunks.all().delete()

        # 3. The Sliding Window Algorithm
        chunk_size = 1000
        overlap = 200
        chunks = []
        
        # Step through the text, going back 200 chars each time
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk = full_text[i:i + chunk_size]
            if len(chunk.strip()) > 50:  # Ignore tiny, useless fragments
                chunks.append(chunk)

        # 4. Generate AI Vectors and Save to Database
        for index, chunk_text in enumerate(chunks):
            # Turn this specific paragraph into math
            vector = get_embedding(chunk_text)
            
            if vector:
                DocumentChunk.objects.create(
                    document=document,
                    chunk_index=index,
                    text_content=chunk_text,
                    embedding=vector
                )

        # 5. Mark Complete and finally add that Preview!
        document.status = 'completed'
        document.analysis_result = {
            "char_count": len(full_text),
            "chunk_count": len(chunks),
            "text_preview": full_text[:200] + "..."  # Grab the first 200 chars
        }
        # We don't strictly need the massive document-level embedding anymore, 
        # but we can leave it null for now.
        document.save()

    except Exception as e:
        if 'document' in locals():
            document.status = 'failed'
            document.analysis_result = {"error": str(e)}
            document.save()