from celery import shared_task
from .models import Document
import PyPDF2
import time

@shared_task
def analyze_document_task(document_id):
    """
    Background task to extract text and analyze a PDF.
    """
    try:
        # 1. Get the Document (and set status to Processing)
        doc = Document.objects.get(id=document_id)
        doc.status = 'processing'
        doc.save()

        print(f"Starting analysis for: {doc.title}")
        
        # 2. Simulate heavy AI work (sleep 3 seconds)
        time.sleep(3)

        # 3. Read the PDF (Real work)
        pdf_reader = PyPDF2.PdfReader(doc.file.path)
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() or ""

        # 4. Perform "Analysis" (Count words)
        word_count = len(text_content.split())
        
        # 5. Save Results (and set status to Completed)
        doc.analysis_result = {
            "word_count": word_count,
            "preview": text_content[:100] + "...",  # First 100 chars
            "sentiment": "Neutral (Mock)"
        }
        doc.status = 'completed'
        doc.save()
        
        print(f"Finished analysis for: {doc.title}")
        return "Analysis Complete"

    except Document.DoesNotExist:
        return "Document not found"
    except Exception as e:
        if 'doc' in locals():
            doc.status = 'failed'
            doc.save()
        print(f"Error analyzing document: {str(e)}")
        return f"Error: {str(e)}"