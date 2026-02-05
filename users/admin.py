from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# This tells Django: "Use the standard User Admin interface for my custom User model"
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # We will customize this later to show 'organization' etc.
    pass