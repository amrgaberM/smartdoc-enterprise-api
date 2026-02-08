from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        # We include the URL of the file, not the raw binary data
        fields = ['id', 'title', 'file', 'created_at']
        # Notice we DO NOT include 'owner'. 
        # Why? Because the user shouldn't be able to say "I am uploading this for Bob."
        # The server will automatically stamp it with their name.