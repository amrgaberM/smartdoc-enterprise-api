import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

# This mark tells pytest: "Allow this test to write to the Test Database"
@pytest.mark.django_db
def test_register_user_api():
    """
    Scenario: A stranger tries to sign up.
    Expected: API returns 201 Created, and User is in the DB.
    """
    # 1. Setup the "Robot" Client
    client = APIClient()
    
    # 2. Prepare the Data
    payload = {
        "email": "robot@test.com",
        "username": "robot",
        "password": "securepassword123"
    }
    
    # 3. Send POST Request (The Action)
    response = client.post('/api/users/', payload)
    
    # 4. Check the Response (The Assertion)
    assert response.status_code == 201
    assert response.data['email'] == "robot@test.com"

    # 5. Check the Database (The Verification)
    User = get_user_model()
    assert User.objects.count() == 1
    assert User.objects.first().email == "robot@test.com"