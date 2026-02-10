from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'uploaded_at')
    # This prevents the "vector must have at least 1 dimension" error in Admin
    exclude = ('embedding',) 
    readonly_fields = ('analysis_result',)