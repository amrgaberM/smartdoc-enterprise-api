from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model()

# Endpoint 1: List all users (GET) or Create a new one (POST)
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    # This view automatically handles:
    # 1. Pagination (User 1-10)
    # 2. Security (Must be logged in)
    # 3. JSON conversion