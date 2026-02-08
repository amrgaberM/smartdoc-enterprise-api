from django.db import models
from django.conf import settings # Use this to reference your CustomUser

class Document(models.Model):
    # 1. The Owner (Foreign Key)
    # If the user is deleted, their files are also deleted (CASCADE)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='documents'
    )

    # 2. The File Details
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='pdfs/') # Save inside a 'pdfs' folder
    created_at = models.DateTimeField(auto_now_add=True)

    # 3. String Representation (for Admin Panel)
    def __str__(self):
        return f"{self.title} ({self.owner.username})"