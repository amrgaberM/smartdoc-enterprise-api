from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        # We also added 'status' and 'analysis_result', so let's include them!
        fields = ('id', 'title', 'file', 'uploaded_at', 'owner', 'status', 'analysis_result')
        read_only_fields = ('owner', 'uploaded_at', 'status', 'analysis_result')