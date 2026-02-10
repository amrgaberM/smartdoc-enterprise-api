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