from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Ensure email is unique and required
    email = models.EmailField(unique=True)

    # THIS IS THE CRITICAL PART:
    # Tell Django to use 'email' as the login identifier
    USERNAME_FIELD = 'email' 
    
    # Username is still required for creation, but not for login
    REQUIRED_FIELDS = ['username'] 

    def __str__(self):
        return self.email