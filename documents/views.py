from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import Document
from .serializers import DocumentSerializer
from .tasks import analyze_document_task

class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser) # Enables file upload

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class DocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

class DocumentAnalyzeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk, owner=request.user)
        analyze_document_task.delay(document.id)
        return Response({"status": "processing"}, status=status.HTTP_202_ACCEPTED)