from django.db import models
from django.conf import settings
from pgvector.django import VectorField 

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    analysis_result = models.JSONField(default=dict, blank=True)

    # 768 dimensions matches the 'all-mpnet-base-v2' model we are using
    embedding = VectorField(dimensions=768, blank=True, null=True)

    def __str__(self):
        return self.title
    
class DocumentChunk(models.Model):
    """
    Stores smaller paragraphs of a document so the AI can search 
    with high precision (avoiding Vector Dilution).
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField(help_text="The order of this paragraph in the document")
    text_content = models.TextField(help_text="The actual text of this paragraph")
    
    # 768 dimensions to match our 'all-mpnet-base-v2' model
    embedding = VectorField(dimensions=768, null=True, blank=True)

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"