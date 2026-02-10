from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    # This line FORCES Swagger to show a "Choose File" button
    file = serializers.FileField() 

    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'uploaded_at', 'status', 'analysis_result']
        read_only_fields = ['id', 'uploaded_at', 'owner', 'status', 'analysis_result']