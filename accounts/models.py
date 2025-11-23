# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save  # ADD THIS IMPORT
from django.dispatch import receiver  # ADD THIS IMPORT
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from django.db.models.signals import post_save
from django.dispatch import receiver
import requests

def geocode_city(city_name):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            loc = data["results"][0]
            return loc["latitude"], loc["longitude"]
        else:
            print(f"No results found in data: {data}")
    except Exception as e:
        print(f"Error geocoding city {city_name}: {e}")
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
    projects = models.TextField(blank=True, null=True, help_text="List of notable projects or portfolio work (comma-separated)")

    # Professional links
    linkedin_url = models.URLField(blank=True, null=True, help_text="Your LinkedIn profile URL")
    github_url = models.URLField(blank=True, null=True, help_text="Your GitHub profile URL")
    portfolio_url = models.URLField(blank=True, null=True, help_text="Your portfolio website URL")
    other_url = models.URLField(blank=True, null=True, help_text="Any other professional link")
    
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
    city = models.CharField(max_length=255, blank=True, null=True, help_text="city for geolocation")
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
        if self.city and (self.latitude is None or self.longitude is None):
            lat, lng = geocode_city(self.city)
            if lat and lng:
                self.latitude = lat
                self.longitude = lng
                print(f"Geocoded city {self.city} → lat: {lat}, lng: {lng}")
            else:
                print(f"Could not geocode city: {self.city}")
        else:
            print("City not provided or already has coordinates.")
        super().save(*args, **kwargs)
    
    def get_email_password(self):
        """Get the decrypted email password"""
        if self.email_host_password and self.email_host_password.startswith('encrypted:'):
            return self.email_host_password.replace('encrypted:', '')
        return self.email_host_password

# SIGNALS - Make sure these are at the bottom
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile automatically when a new User is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile automatically when User is saved"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # If profile doesn't exist, create it
        UserProfile.objects.get_or_create(user=instance)
