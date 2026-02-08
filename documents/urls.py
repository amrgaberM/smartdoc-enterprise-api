from django.urls import path
from .views import DocumentListCreateView, DocumentDetailView, DocumentAnalyzeView # <--- Import

urlpatterns = [
    path('', DocumentListCreateView.as_view(), name='document-list-create'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    
    # NEW PATH: The "Trigger" Button
    path('<int:pk>/analyze/', DocumentAnalyzeView.as_view(), name='document-analyze'),
]