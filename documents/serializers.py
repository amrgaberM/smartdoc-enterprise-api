from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        # Add the new AI fields here so they appear in the JSON
        fields = [
            'id', 
            'title', 
            'file', 
            'created_at', 
            'is_analyzed', 
            'ai_summary', 
            'ai_sentiment'
        ]
        # Optional: Make sure users can't edit these fields manually
        read_only_fields = ['is_analyzed', 'ai_summary', 'ai_sentiment']