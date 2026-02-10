from celery import shared_task
from .models import Document
import time
import PyPDF2
import logging

# Set up a logger to print errors to the console
logger = logging.getLogger(__name__)

@shared_task
def analyze_document_task(document_id):
    """
    Background task to analyze a document.
    Handles errors gracefully by updating the status to 'failed'.
    """
    logger.info(f"--- WORKER: Starting analysis for Document {document_id} ---")
    
    try:
        # 1. Get the Document
        doc = Document.objects.get(id=document_id)
        doc.status = 'processing'
        doc.save()

        # 2. Simulate "Heavy AI" Work (Wait 2 seconds)
        time.sleep(2)

        # 3. Extract Text (The "Real" Work)
        try:
            # Open the file directly from the storage path
            with doc.file.open('rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                
                # Extract text from all pages
                for page in reader.pages:
                    text += page.extract_text() or ""
                
                # Check if file was empty or just images
                if not text.strip():
                    raise ValueError("No text found. PDF might be an image scan or empty.")
                
                word_count = len(text.split())
                preview = text[:200] + "..." if len(text) > 200 else text

        except Exception as file_error:
            # Catch specific PDF errors (corrupted file, wrong format)
            raise ValueError(f"PDF Error: {str(file_error)}")

        # 4. Success! Save results.
        doc.analysis_result = {
            "word_count": word_count,
            "preview": preview,
            "sentiment": "Neutral (Mock Analysis)"
        }
        doc.status = 'completed'
        doc.save()
        logger.info(f"--- WORKER: SUCCESS Document {document_id} ---")
        return "Analysis Complete"

    except Document.DoesNotExist:
        return "Error: Document not found"
    
    except Exception as e:
        # 5. FAILURE CASE: Update DB so user knows it failed!
        logger.error(f"--- WORKER: FAILED Document {document_id} -> {e} ---")
        try:
            # Re-fetch doc to avoid stale data
            doc = Document.objects.get(id=document_id)
            doc.status = 'failed'
            doc.analysis_result = {"error": str(e)}
            doc.save()
        except:
            pass # If DB is unreachable, we can't do anything
        return f"Failed: {e}"