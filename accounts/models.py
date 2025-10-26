from django.db import models
from django.contrib.auth.models import User
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def geocode_zip(zip_code):
    try:
        geolocator = Nominatim(user_agent="job_map_app")
        location = geolocator.geocode(zip_code)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Error geocoding ZIP code {zip_code}: {e}")
    return None, None

class UserProfile(models.Model):
    """Simple user profile with privacy controls"""
    
    USER_TYPE_CHOICES = [
        ('user', 'Job Seeker'),
        ('recruiter', 'Recruiter'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', 'Public - Visible to all recruiters'),
        ('private', 'Private - Only visible to you'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # User type - cannot be changed after signup
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPE_CHOICES, 
        default='user',
        help_text="Account type - cannot be changed after signup"
    )
    
    # Basic info
    bio = models.TextField(blank=True, null=True, help_text="Tell us about yourself")
    experience = models.TextField(blank=True, null=True, help_text="Your work experience")
    education = models.TextField(blank=True, null=True, help_text="Your education background")
    skills = models.TextField(blank=True, null=True, help_text="Your skills (comma-separated)")
    
    # Privacy settings - MOST IMPORTANT
    profile_privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='private')
    allow_recruiters_to_contact = models.BooleanField(default=False, help_text="Allow recruiters to contact you")
    
    #location
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
