from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle
from pgvector.django import CosineDistance
from django.db.models import Prefetch
import logging

from .models import Document, DocumentChunk
from .serializers import DocumentSerializer
from .tasks import analyze_document_task
from .embeddings import get_embedding
from .llm_utils import generate_answer, generate_multi_document_answer, validate_context_quality

# Setup logging
logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    Enhanced DocumentViewSet with optimized queries and better error handling.
    
    Endpoints:
    - GET /documents/ - List user's documents
    - POST /documents/ - Upload new document
    - GET /documents/{id}/ - Retrieve specific document
    - PUT/PATCH /documents/{id}/ - Update document
    - DELETE /documents/{id}/ - Delete document
    - POST /documents/{id}/analyze/ - Start background analysis
    - POST /documents/{id}/ask/ - Ask question about specific document
    - POST /documents/global_ask/ - Search across all documents
    """
    
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, ScopedRateThrottle]
    throttle_scope = None  # Default scope (uses 'user' rate)

    def get_queryset(self):
        """
        Optimized queryset with prefetching to reduce database queries.
        Only returns documents owned by the current user.
        """
        return Document.objects.filter(
            owner=self.request.user
        ).select_related(
            'owner'
        ).prefetch_related(
            Prefetch(
                'chunks',
                queryset=DocumentChunk.objects.only('id', 'chunk_index')
            )
        ).order_by('-uploaded_at')

    def perform_create(self, serializer):
        """
        Automatically set the document owner to the authenticated user.
        """
        document = serializer.save(owner=self.request.user)
        logger.info(f"Document created: {document.id} by user {self.request.user.id}")

    def destroy(self, request, *args, **kwargs):
        """
        Enhanced delete with cleanup logging.
        """
        document = self.get_object()
        document_id = document.id
        document_title = document.title
        
        # Perform deletion
        response = super().destroy(request, *args, **kwargs)
        
        logger.info(f"Document deleted: {document_id} ('{document_title}') by user {request.user.id}")
        return response

    # ========================================================================
    # DOCUMENT ANALYSIS ENDPOINT
    # ========================================================================
    
    @action(
        detail=True, 
        methods=['post'],
        throttle_scope='uploads'  # Uses upload rate limit (5/min)
    )
    def analyze(self, request, pk=None):
        """
        Trigger background analysis for a document.
        
        Request:
            POST /documents/{id}/analyze/
        
        Response:
            202 - Analysis started
            400 - Document already processing
            404 - Document not found
        """
        document = self.get_object()
        
        # Check if already processing
        if document.status == 'processing':
            return Response(
                {
                    "message": "Document is already being analyzed.",
                    "status": document.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already completed
        if document.status == 'completed':
            return Response(
                {
                    "message": "Document has already been analyzed. Re-analyzing...",
                    "status": "processing"
                },
                status=status.HTTP_202_ACCEPTED
            )
        
        # Start analysis
        document.status = 'processing'
        document.save(update_fields=['status'])
        
        # Trigger Celery task
        analyze_document_task.delay(document.id)
        
        logger.info(f"Analysis started for document {document.id}")
        
        return Response(
            {
                "message": "Document analysis started. This may take 30-60 seconds.",
                "status": "processing",
                "document_id": document.id
            },
            status=status.HTTP_202_ACCEPTED
        )

    # ========================================================================
    # SINGLE-DOCUMENT CHAT ENDPOINT
    # ========================================================================
    
    @action(
        detail=True, 
        methods=['post'], 
        throttle_scope='ai_chat'  # 20 requests/minute
    )
    def ask(self, request, pk=None):
        """
        Ask a question about a specific document using RAG.
        
        Request:
            POST /documents/{id}/ask/
            Body: {"question": "What is this about?"}
        
        Response:
            200 - Answer with sources
            400 - Invalid request
            404 - No content found
            500 - AI processing error
        """
        document = self.get_object()
        question = request.data.get('question', '').strip()
        
        # Validate input
        if not question:
            return Response(
                {"error": "Question is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(question) > 500:
            return Response(
                {"error": "Question exceeds 500 character limit"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check document status
        if document.status != 'completed':
            return Response(
                {
                    "error": f"Document is not ready for questions. Status: {document.status}",
                    "status": document.status,
                    "suggestion": "Please wait for analysis to complete or trigger analysis if status is 'pending'."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate embedding for the question
            query_vector = get_embedding(question)
            
            if not query_vector:
                logger.error(f"Failed to generate embedding for question: {question[:50]}...")
                return Response(
                    {"error": "Failed to process your question. Please try again."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Retrieve most relevant chunks
            context_chunks = DocumentChunk.objects.filter(
                document=document
            ).annotate(
                distance=CosineDistance('embedding', query_vector)
            ).order_by('distance')[:3]  # Top 3 most relevant chunks
            
            # Validate context quality
            is_valid, reason = validate_context_quality(question, context_chunks)
            
            if not is_valid:
                return Response(
                    {
                        "answer": f"I couldn't find relevant information to answer your question. {reason}",
                        "sources": [],
                        "confidence": "low"
                    },
                    status=status.HTTP_200_OK
                )
            
            # Generate answer using enhanced LLM
            answer = generate_answer(question, context_chunks)
            
            # Calculate average confidence
            avg_similarity = sum(1 - float(c.distance) for c in context_chunks) / len(context_chunks)
            confidence = "high" if avg_similarity > 0.7 else "medium" if avg_similarity > 0.5 else "low"
            
            # Prepare sources for response
            sources = [{
                "page": chunk.chunk_index + 1,
                "text": chunk.text_content[:200],  # First 200 chars
                "relevance": round(1 - float(chunk.distance), 2)
            } for chunk in context_chunks]
            
            logger.info(f"Question answered for document {document.id}, confidence: {confidence}")
            
            return Response({
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "chunks_used": len(context_chunks)
            })
            
        except Exception as e:
            logger.error(f"Error in ask endpoint for document {document.id}: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": "An unexpected error occurred while processing your question.",
                    "detail": str(e) if request.user.is_staff else None  # Only show details to staff
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ========================================================================
    # GLOBAL MULTI-DOCUMENT SEARCH ENDPOINT
    # ========================================================================
    
    @action(
        detail=False, 
        methods=['post'], 
        throttle_scope='ai_chat'  # 20 requests/minute
    )
    def global_ask(self, request):
        """
        Search and answer questions across all user's documents.
        
        Request:
            POST /documents/global_ask/
            Body: {"question": "What themes appear across my documents?"}
        
        Response:
            200 - Answer with multi-document sources
            400 - Invalid request
            404 - No analyzed documents found
            500 - AI processing error
        """
        question = request.data.get('question', '').strip()
        
        # Validate input
        if not question:
            return Response(
                {"error": "Question is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(question) > 500:
            return Response(
                {"error": "Question exceeds 500 character limit"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate embedding
            query_vector = get_embedding(question)
            
            if not query_vector:
                logger.error(f"Failed to generate embedding for global question: {question[:50]}...")
                return Response(
                    {"error": "Failed to process your question. Please try again."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Retrieve top chunks across ALL completed documents
            context_chunks = DocumentChunk.objects.filter(
                document__owner=request.user,
                document__status='completed'
            ).select_related(
                'document'
            ).annotate(
                distance=CosineDistance('embedding', query_vector)
            ).order_by('distance')[:5]  # Top 5 across all documents
            
            # Check if user has any analyzed documents
            if not context_chunks.exists():
                completed_count = Document.objects.filter(
                    owner=request.user,
                    status='completed'
                ).count()
                
                if completed_count == 0:
                    return Response(
                        {
                            "error": "No analyzed documents found. Please upload and analyze documents first.",
                            "suggestion": "Upload a PDF and click 'Analyze' to enable global search."
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    return Response(
                        {
                            "answer": "I couldn't find relevant information across your documents to answer this question.",
                            "sources": [],
                            "documents_searched": completed_count
                        },
                        status=status.HTTP_200_OK
                    )
            
            # Validate context quality
            is_valid, reason = validate_context_quality(question, context_chunks)
            
            if not is_valid:
                return Response(
                    {
                        "answer": f"I found some content but it's not sufficient to answer your question. {reason}",
                        "sources": [],
                        "confidence": "low"
                    },
                    status=status.HTTP_200_OK
                )
            
            # Generate answer using multi-document LLM
            answer = generate_multi_document_answer(question, context_chunks)
            
            # Calculate confidence
            avg_similarity = sum(1 - float(c.distance) for c in context_chunks) / len(context_chunks)
            confidence = "high" if avg_similarity > 0.7 else "medium" if avg_similarity > 0.5 else "low"
            
            # Get unique documents
            unique_docs = set(c.document.id for c in context_chunks)
            
            # Prepare sources with document info
            sources = [{
                "document_id": chunk.document.id,
                "document_title": chunk.document.title,
                "page": chunk.chunk_index + 1,
                "text": chunk.text_content[:200],
                "relevance": round(1 - float(chunk.distance), 2)
            } for chunk in context_chunks]
            
            logger.info(
                f"Global search answered for user {request.user.id}, "
                f"{len(unique_docs)} documents, confidence: {confidence}"
            )
            
            return Response({
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "documents_searched": len(unique_docs),
                "chunks_used": len(context_chunks)
            })
            
        except Exception as e:
            logger.error(f"Error in global_ask endpoint: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": "An unexpected error occurred while searching your documents.",
                    "detail": str(e) if request.user.is_staff else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ========================================================================
    # OPTIONAL: GET DOCUMENT STATISTICS
    # ========================================================================
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get detailed statistics about a document.
        
        Request:
            GET /documents/{id}/stats/
        
        Response:
            Document metadata and analysis statistics
        """
        document = self.get_object()
        
        # Count chunks
        chunk_count = document.chunks.count()
        
        # Get analysis results
        analysis = document.analysis_result or {}
        
        return Response({
            "document_id": document.id,
            "title": document.title,
            "status": document.status,
            "uploaded_at": document.uploaded_at,
            "file_size": getattr(document.file, 'size', None),
            "analysis": {
                "page_count": analysis.get('page_count'),
                "word_count": analysis.get('word_count'),
                "char_count": analysis.get('char_count'),
                "chunk_count": chunk_count,
                "has_summary": bool(analysis.get('insights') or analysis.get('summary')),
            },
            "processing_info": {
                "can_ask_questions": document.status == 'completed' and chunk_count > 0,
                "error": analysis.get('error') if document.status == 'failed' else None
            }
        })
    
    # ========================================================================
    # OPTIONAL: BATCH ANALYSIS
    # ========================================================================
    
    @action(detail=False, methods=['post'])
    def analyze_all(self, request):
        """
        Trigger analysis for all pending documents.
        
        Request:
            POST /documents/analyze_all/
        
        Response:
            Number of documents queued for analysis
        """
        pending_docs = Document.objects.filter(
            owner=request.user,
            status='pending'
        )
        
        count = pending_docs.count()
        
        if count == 0:
            return Response(
                {"message": "No pending documents to analyze"},
                status=status.HTTP_200_OK
            )
        
        # Update all to processing
        pending_docs.update(status='processing')
        
        # Queue all for analysis
        for doc in pending_docs:
            analyze_document_task.delay(doc.id)
        
        logger.info(f"Batch analysis started for {count} documents by user {request.user.id}")
        
        return Response(
            {
                "message": f"Started analysis for {count} document(s)",
                "count": count
            },
            status=status.HTTP_202_ACCEPTED
        )