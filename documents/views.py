from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from pgvector.django import CosineDistance

from .models import Document, DocumentChunk  # Ensure both are imported
from .serializers import DocumentSerializer
from .tasks import analyze_document_task
from .embeddings import get_embedding
from .llm_utils import generate_answer

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user).order_by('-uploaded_at')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        document = self.get_object()
        if document.status in ['processing', 'completed']:
            return Response(
                {"message": f"Document is already {document.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        analyze_document_task.delay(document.id)
        return Response(
            {"message": "Analysis started in the background."},
            status=status.HTTP_202_ACCEPTED
        )

    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        UPGRADED: Searches through individual DocumentChunks for high precision.
        """
        query_text = request.data.get('query')
        if not query_text:
            return Response(
                {"error": "Please provide a 'query' field."},
                status=status.HTTP_400_BAD_REQUEST
            )

        query_vector = get_embedding(query_text)
        if not query_vector:
            return Response(
                {"error": "Failed to generate AI embedding."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # THE UPGRADE: We search DocumentChunk and filter by the owner of the document
        chunks = DocumentChunk.objects.filter(
            document__owner=request.user
        ).annotate(
            distance=CosineDistance('embedding', query_vector)
        ).order_by('distance')[:5]

        response_data = []
        for chunk in chunks:
            response_data.append({
                "document_title": chunk.document.title,
                "chunk_index": chunk.chunk_index,
                "distance": round(chunk.distance, 4),
                "text": chunk.text_content[:300] + "..." # Returns the actual relevant text!
            })

        return Response({"results": response_data}, status=status.HTTP_200_OK)
    @action(detail=True, methods=['post'])
    def ask(self, request, pk=None):
        """
        Full RAG: Retrieve relevant chunks and generate an answer using Groq.
        """
        document = self.get_object()
        question = request.data.get('question')

        if not question:
            return Response({"error": "Please provide a question."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Vectorize the user's question
        query_vector = get_embedding(question)
        
        # 2. Retrieve the top 3 most relevant chunks ONLY for THIS document
        context_chunks = DocumentChunk.objects.filter(
            document=document
        ).annotate(
            distance=CosineDistance('embedding', query_vector)
        ).order_by('distance')[:3]

        if not context_chunks.exists():
            return Response({"error": "No processed content found for this document. Please analyze it first."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Generate the answer using Groq (The Brain)
        try:
            answer = generate_answer(question, context_chunks)
            
            return Response({
                "question": question,
                "answer": answer,
                "sources": [
                    {"index": c.chunk_index, "distance": round(c.distance, 4)} 
                    for c in context_chunks
                ]
            })
        except Exception as e:
            return Response({"error": f"LLM Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)