from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet

# A Router automatically generates the URLs for our ViewSet
router = DefaultRouter()
# If your base URL is already api/documents/, this will map correctly.
router.register(r'', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]