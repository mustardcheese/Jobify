from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ("full_time", "Full Time"),
        ("part_time", "Part Time"),
        ("contract", "Contract"),
        ("internship", "Internship"),
        ("remote", "Remote"),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("entry", "Entry Level"),
        ("mid", "Mid Level"),
        ("senior", "Senior Level"),
        ("lead", "Lead"),
    ]

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    salary_range = models.CharField(max_length=100, blank=True)
    job_type = models.CharField(
        max_length=20, choices=JOB_TYPE_CHOICES, default="full_time"
    )
    experience_level = models.CharField(
        max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default="mid"
    )
    posted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    employer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="posted_jobs",
        null=True,  # Make nullable for existing data
        blank=True
    )
    application_email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

    def save(self, *args, **kwargs):
        # Auto-set employer if not set and we have a request user (handled in views)
        if not self.employer and hasattr(self, '_current_user'):
            self.employer = self._current_user
        super().save(*args, **kwargs)


class Application(models.Model):
    APPLICATION_STATUS_CHOICES = [
        ("applied", "Applied"),
        ("reviewed", "Reviewed"),
        ("interview", "Interview"),
        ("offer", "Offer"),
        ("closed", "Closed"),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="job_applications"
    )
    application_note = models.TextField(
        help_text="Why are you interested in this position?"
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=APPLICATION_STATUS_CHOICES, default="applied"
    )
    resume = models.FileField(upload_to="resumes/", blank=True, null=True)

    class Meta:
        unique_together = ["job", "applicant"]

    def __str__(self):
        return f"Application for {self.job.title} by {self.applicant.username}"


class Message(models.Model):
    MESSAGE_TYPES = [
        ('application', 'Application Related'),
        ('interview', 'Interview Invitation'),
        ('offer', 'Job Offer'),
        ('general', 'General Inquiry'),
        ('rejection', 'Rejection'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    application = models.ForeignKey(
        Application, 
        on_delete=models.CASCADE, 
        related_name='messages', 
        null=True, 
        blank=True
    )
    subject = models.CharField(max_length=200)
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='application')
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} - {self.subject}"

    @property
    def sender_is_recruiter(self):
        """Check if sender is a recruiter using the existing UserProfile"""
        return hasattr(self.sender, 'profile') and self.sender.profile.user_type == 'recruiter'

    @property
    def recipient_is_recruiter(self):
        """Check if recipient is a recruiter using the existing UserProfile"""
        return hasattr(self.recipient, 'profile') and self.recipient.profile.user_type == 'recruiter'
