from rest_framework import generics, permissions
from .models import Document
from .serializers import DocumentSerializer

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