from django.contrib import admin
from .models import Job, Application

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'job_type', 'experience_level', 'salary_range', 'posted_at', 'is_active']
    list_filter = ['job_type', 'experience_level', 'company', 'location', 'posted_at', 'is_active']
    search_fields = ['title', 'company', 'location', 'description']
    list_editable = ['is_active']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['title', 'company', 'location', 'is_active']
        }),
        ('Job Details', {
            'fields': ['job_type', 'experience_level', 'salary_range']
        }),
        ('Description & Requirements', {
            'fields': ['description', 'requirements']
        }),
        ('Location Coordinates (for map)', {
            'fields': ['latitude', 'longitude'],
            'classes': ['collapse']
        }),
    ]

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'applicant', 'applied_at', 'status']
    list_filter = ['status', 'applied_at', 'job__company']
    search_fields = ['applicant__username', 'job__title', 'application_note']
    list_editable = ['status']
    readonly_fields = ['applied_at']