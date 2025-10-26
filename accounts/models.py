# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
    
    # Contact email for all users
    email = models.EmailField(
        blank=True, 
        null=True, 
        help_text="Your contact email address"
    )
    
    # Basic info
    bio = models.TextField(blank=True, null=True, help_text="Tell us about yourself")
    experience = models.TextField(blank=True, null=True, help_text="Your work experience")
    education = models.TextField(blank=True, null=True, help_text="Your education background")
    skills = models.TextField(blank=True, null=True, help_text="Your skills (comma-separated)")
    
    # Privacy settings - MOST IMPORTANT
    profile_privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='private')
    allow_recruiters_to_contact = models.BooleanField(default=False, help_text="Allow recruiters to contact you")
    
    # NEW: Email settings for recruiters (Gmail configuration)
    email_host = models.CharField(max_length=255, default='smtp.gmail.com', blank=True)
    email_port = models.IntegerField(default=587, blank=True)
    email_use_tls = models.BooleanField(default=True)
    email_host_user = models.EmailField(blank=True, null=True, help_text="Gmail address for sending emails")
    email_host_password = models.CharField(max_length=255, blank=True, null=True, help_text="Gmail App Password")
    email_configured = models.BooleanField(default=False, help_text="Gmail is configured for sending emails")
    
    
    #location
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    # NEW: Property to check if recruiter has email setup
    @property
    def has_email_setup(self):
        """Check if user has email configured for their role"""
        if self.user_type == 'recruiter':
            return self.email_configured and self.email_host_user
        else:
            return bool(self.email)  # Job seekers just need a contact email
    
    def save(self, *args, **kwargs):
        # Simple encryption for password (basic security)
        if self.email_host_password and not self.email_host_password.startswith('encrypted:'):
            # In a real app, you'd use proper encryption here
            # For now, we'll just mark it as encrypted
            self.email_host_password = f"encrypted:{self.email_host_password}"
        super().save(*args, **kwargs)
    
    def get_email_password(self):
        """Get the decrypted email password"""
        if self.email_host_password and self.email_host_password.startswith('encrypted:'):
            return self.email_host_password.replace('encrypted:', '')
        return self.email_host_password