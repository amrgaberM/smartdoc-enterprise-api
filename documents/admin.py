from django.contrib import admin
from .models import Document, DocumentChunk

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'uploaded_at')
    # This prevents the "vector must have at least 1 dimension" error in Admin
    exclude = ('embedding',) 
    readonly_fields = ('analysis_result',)

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'short_text')
    # Exclude the vector math here too!
    exclude = ('embedding',)
    
    # Show just a snippet of the chunk in the list view
    def short_text(self, obj):
        return obj.text_content[:75] + "..." if obj.text_content else ""
    short_text.short_description = 'Text Preview'