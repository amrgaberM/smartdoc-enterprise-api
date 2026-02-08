from rest_framework import generics, permissions
from .models import Document
from .serializers import DocumentSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .ai_engine import AIEngine

class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated] # Lock the door

    # 1. SECURITY: Filter the list
    def get_queryset(self):
        # "Select * FROM documents WHERE owner = [Current User]"
        return Document.objects.filter(owner=self.request.user)

    # 2. AUTOMATION: Stamp the owner
    def perform_create(self, serializer):
        # When saving, manually add the 'owner' field using the logged-in user
        serializer.save(owner=self.request.user)

# ... keep your existing imports and DocumentListCreateView ...

# NEW VIEW: Handles GET (Retrieve one), PUT (Update), and DELETE (Destroy)
class DocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # SECURITY: Only let users touch their OWN files
        return Document.objects.filter(owner=self.request.user)


# ... keep existing views ...

class DocumentAnalyzeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # 1. Get the Document (and ensure I own it)
        document = get_object_or_404(Document, pk=pk, owner=request.user)

        # 2. Extract Text (The Eyes)
        text = AIEngine.extract_text(document.file.path)
        if text.startswith("Error"):
            return Response({"error": text}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Analyze Text (The Brain)
        analysis = AIEngine.analyze(text)

        # 4. Save Results (The Memory)
        document.ai_summary = analysis['summary']
        document.ai_sentiment = analysis['sentiment']
        document.is_analyzed = True
        document.save()

        # 5. Return Success
        return Response({
            "status": "Analysis Complete",
            "summary": document.ai_summary,
            "sentiment": document.ai_sentiment
        })
    

    def get(self, request, pk):
        # This function exists JUST to let the API page load in the browser
        return Response({
            "info": "This endpoint is for AI Analysis.",
            "instruction": "Click the POST button below to analyze this document."
        })