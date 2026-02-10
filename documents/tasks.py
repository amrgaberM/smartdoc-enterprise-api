import fitz  # PyMuPDF
from celery import shared_task
from sentence_transformers import SentenceTransformer
from .models import Document

@shared_task
def analyze_document_task(document_id):
    try:
        doc_obj = Document.objects.get(id=document_id)
        doc_obj.status = 'processing'
        doc_obj.save()

        # 1. Extract Text
        text = ""
        with fitz.open(doc_obj.file.path) as pdf:
            for page in pdf:
                text += page.get_text()

        # 2. Generate Embedding (Size 768)
        model = SentenceTransformer('all-mpnet-base-v2')
        embedding = model.encode(text).tolist()

        # 3. Save Results
        doc_obj.embedding = embedding
        doc_obj.analysis_result = {
            "char_count": len(text),
            "embedding_generated": True
        }
        doc_obj.status = 'completed'
        doc_obj.save()
        
        return f"Document {document_id} analyzed successfully."

    except Exception as e:
        Document.objects.filter(id=document_id).update(
            status='failed',
            analysis_result={"error": str(e)}
        )
        return f"Error: {str(e)}"