from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # We only expose safe fields. Never expose 'password'!
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'is_active', 'date_joined']