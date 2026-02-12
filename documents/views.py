from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle
from pgvector.django import CosineDistance

from .models import Document, DocumentChunk
from .serializers import DocumentSerializer
from .tasks import analyze_document_task
from .embeddings import get_embedding
from .llm_utils import generate_answer

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    # SECURITY: Add Rate Limiting
    throttle_classes = [UserRateThrottle, ScopedRateThrottle] 
    
    # --- FIX IS HERE: Define default scope to avoid TypeError ---
    throttle_scope = None 

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user).order_by('-uploaded_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        document = self.get_object()
        if document.status == 'processing':
            return Response({"message": "Document is already being processed."}, status=400)

        document.status = 'processing'
        document.save()
        analyze_document_task.delay(document.id)
        return Response({"message": "Analysis started in background."}, status=status.HTTP_202_ACCEPTED)

    # Protected by 'ai_chat' scope limit
    @action(detail=True, methods=['post'], throttle_scope='ai_chat') 
    def ask(self, request, pk=None):
        document = self.get_object()
        question = request.data.get('question')
        
        if not question:
            return Response({"error": "No question provided"}, status=400)

        query_vector = get_embedding(question)
        if not query_vector:
             return Response({"error": "Failed to generate embedding"}, status=500)

        context_chunks = DocumentChunk.objects.filter(
            document=document
        ).annotate(
            distance=CosineDistance('embedding', query_vector)
        ).order_by('distance')[:3]

        if not context_chunks.exists():
            return Response({"error": "No content found. Did you analyze the document?"}, status=404)

        try:
            answer = generate_answer(question, context_chunks)
            sources = [{
                "page": c.chunk_index + 1,
                "text": c.text_content[:200],
                "score": round(1 - float(c.distance), 2)
            } for c in context_chunks]

            return Response({"answer": answer, "sources": sources})
        except Exception as e:
            return Response({"error": f"AI Error: {str(e)}"}, status=500)

    # Protected by 'ai_chat' scope limit
    @action(detail=False, methods=['post'], throttle_scope='ai_chat') 
    def global_ask(self, request):
        question = request.data.get('question')
        if not question:
            return Response({"error": "No question provided"}, status=400)

        query_vector = get_embedding(question)
        if not query_vector:
             return Response({"error": "Failed to generate embedding"}, status=500)

        context_chunks = DocumentChunk.objects.filter(
            document__owner=request.user,
            document__status='completed'
        ).annotate(
            distance=CosineDistance('embedding', query_vector)
        ).order_by('distance')[:5]

        if not context_chunks.exists():
            return Response({"error": "No knowledge found. Upload and analyze documents first."}, status=404)

        try:
            answer = generate_answer(question, context_chunks)
            sources = [{
                "document_id": c.document.id,
                "document_title": c.document.title,
                "page": c.chunk_index + 1,
                "text": c.text_content[:200],
                "score": round(1 - float(c.distance), 2)
            } for c in context_chunks]

            return Response({
                "answer": answer,
                "sources": sources
            })
        except Exception as e:
             return Response({"error": f"AI Error: {str(e)}"}, status=500)