from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'uploaded_at', 'status') # Added status too!
    list_filter = ('uploaded_at', 'status')