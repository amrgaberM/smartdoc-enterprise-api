from django.urls import path
from .views import DocumentListCreateView, DocumentDetailView, DocumentAnalyzeView

urlpatterns = [
    path('', DocumentListCreateView.as_view(), name='document-list-create'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('<int:pk>/analyze/', DocumentAnalyzeView.as_view(), name='document-analyze'),
]