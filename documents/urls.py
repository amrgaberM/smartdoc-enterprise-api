from django.urls import path
from .views import DocumentListCreateView, DocumentDetailView # <--- Import it

urlpatterns = [
    path('', DocumentListCreateView.as_view(), name='document-list-create'),
    
    # NEW PATH: /api/documents/3/
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
]