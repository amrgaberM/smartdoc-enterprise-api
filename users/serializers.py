from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password # Import the hasher!

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        # 1. Manually hash the password string
        hashed_password = make_password(validated_data['password'])
        
        # 2. Create the user object directly
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            password=hashed_password,
            is_active=True
        )
        return user