import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.models import Document

@pytest.mark.django_db
def test_upload_document_api():
    """
    Scenario: A logged-in user uploads a PDF.
    Expected: API returns 201 Created, and Document exists in DB.
    """
    # 1. Setup User and Client
    User = get_user_model()
    user = User.objects.create_user(username="amr_test", email="amr@test.com", password="password123")
    
    client = APIClient()
    client.force_authenticate(user=user)  # <--- Magic! Logs the user in instantly without a token.

    # 2. Create a "Fake" PDF File (in memory)
    fake_pdf = SimpleUploadedFile(
        "test_file.pdf", 
        b"This is a fake PDF content", 
        content_type="application/pdf"
    )

    # 3. Send POST Request
    payload = {
        "title": "My Important Doc",
        "file": fake_pdf
    }
    # Note: format='multipart' is required for file uploads
    response = client.post('/api/documents/', payload, format='multipart')

    # 4. Assertions (The Check)
    assert response.status_code == 201
    assert Document.objects.count() == 1
    assert Document.objects.first().title == "My Important Doc"
    assert Document.objects.first().owner == user