from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PipelineStage(models.Model):
    """Kanban board stages for organizing applicants"""
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    job = models.ForeignKey('Job', on_delete=models.CASCADE, related_name='pipeline_stages')
    color = models.CharField(max_length=7, default='#3498db')  # Hex color
    
    class Meta:
        ordering = ['job', 'order']
        unique_together = ['job', 'order']
    
    def __str__(self):
        return f"{self.job.title} - {self.name}"
    
    def save(self, *args, **kwargs):
        # If this is a new instance and no order is set, set it to the next available order
        if not self.pk and self.order == 0:
            last_stage = PipelineStage.objects.filter(job=self.job).order_by('-order').first()
            self.order = last_stage.order + 1 if last_stage else 0
        super().save(*args, **kwargs)


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
        null=True,
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
    
    def get_pipeline_url(self):
        from django.urls import reverse
        return reverse('job_pipeline', kwargs={'pk': self.pk})
    
    def create_default_pipeline_stages(self):
        """Create default pipeline stages for this job"""
        default_stages = [
            {'name': 'Applied', 'order': 0, 'color': '#3498db'},
            {'name': 'Screening', 'order': 1, 'color': '#9b59b6'},
            {'name': 'Interview', 'order': 2, 'color': '#f39c12'},
            {'name': 'Offer', 'order': 3, 'color': '#2ecc71'},
            {'name': 'Hired', 'order': 4, 'color': '#27ae60'},
            {'name': 'Rejected', 'order': 5, 'color': '#e74c3c'},
        ]
        
        for stage_data in default_stages:
            PipelineStage.objects.get_or_create(
                job=self,
                name=stage_data['name'],
                defaults={
                    'order': stage_data['order'],
                    'color': stage_data['color']
                }
            )


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
        ordering = ['-applied_at']

    def __str__(self):
        return f"Application for {self.job.title} by {self.applicant.username}"

    # Properties to get candidate's current email from profile
    @property
    def candidate_email(self):
        """Get the candidate's current email from their profile"""
        return self.applicant.profile.email if hasattr(self.applicant, 'profile') and self.applicant.profile.email else None
    
    @property 
    def candidate_has_email(self):
        """Check if candidate currently has an email"""
        return bool(self.candidate_email)
    
    @property
    def candidate_name(self):
        """Get candidate's name (username as fallback)"""
        if hasattr(self.applicant, 'profile') and self.applicant.profile.bio:
            return self.applicant.profile.bio
        return self.applicant.get_full_name() or self.applicant.username
    
    # Pipeline properties
    @property
    def current_pipeline_stage(self):
        """Get current pipeline stage for this application"""
        try:
            return self.pipeline.current_stage
        except ApplicantPipeline.DoesNotExist:
            return None
    
    @property
    def pipeline_info(self):
        """Get pipeline information"""
        try:
            return self.pipeline
        except ApplicantPipeline.DoesNotExist:
            return None
    
    def create_pipeline_entry(self):
        """Create pipeline entry for this application"""
        # Check if pipeline already exists
        if hasattr(self, 'pipeline'):
            return self.pipeline
        
        first_stage = PipelineStage.objects.filter(
            job=self.job
        ).order_by('order').first()
        
        if first_stage:
            pipeline, created = ApplicantPipeline.objects.get_or_create(
                application=self,
                defaults={'current_stage': first_stage}
            )
            return pipeline
        return None


class ApplicantPipeline(models.Model):
    """Track applicant position in the hiring pipeline"""
    application = models.OneToOneField(
        Application, 
        on_delete=models.CASCADE, 
        related_name='pipeline'
    )
    current_stage = models.ForeignKey(
        PipelineStage, 
        on_delete=models.CASCADE, 
        related_name='applicants'
    )
    previous_stages = models.ManyToManyField(
        PipelineStage, 
        related_name='moved_from_applicants', 
        blank=True
    )
    date_moved = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Internal notes about this candidate")
    
    class Meta:
        ordering = ['-date_moved']
    
    def __str__(self):
        return f"{self.application.applicant.username} - {self.current_stage.name}"
    
    def move_to_stage(self, new_stage):
        """Move applicant to a new stage and update history"""
        if self.current_stage != new_stage:
            self.previous_stages.add(self.current_stage)
            self.current_stage = new_stage
            self.save()
    
    def get_stage_history(self):
        """Get chronological history of stage movements"""
        return self.previous_stages.all().order_by('pipelinetransition__moved_at')


class PipelineTransition(models.Model):
    """Track detailed history of stage transitions"""
    applicant_pipeline = models.ForeignKey(
        ApplicantPipeline, 
        on_delete=models.CASCADE, 
        related_name='transitions'
    )
    from_stage = models.ForeignKey(
        PipelineStage, 
        on_delete=models.CASCADE, 
        related_name='transitions_from'
    )
    to_stage = models.ForeignKey(
        PipelineStage, 
        on_delete=models.CASCADE, 
        related_name='transitions_to'
    )
    moved_at = models.DateTimeField(auto_now_add=True)
    moved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='pipeline_moves'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-moved_at']


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
    
    # FIELDS FOR EMAIL FUNCTIONALITY
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_failed = models.BooleanField(default=False)
    email_failure_reason = models.TextField(blank=True)
    
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

    # METHOD FOR EMAIL STATUS
    @property
    def email_status(self):
        """Get human-readable email status"""
        if self.email_sent:
            return f"Sent {self.email_sent_at.strftime('%b %d, %Y %H:%M')}" if self.email_sent_at else "Sent"
        elif self.email_failed:
            return "Failed"
        else:
            return "Not Sent"
    
    @property
    def recipient_email(self):
        """Get recipient's current email from their profile"""
        return self.recipient.profile.email if hasattr(self.recipient, 'profile') and self.recipient.profile.email else None
    
    @property
    def recipient_has_email(self):
        """Check if recipient currently has an email"""
        return bool(self.recipient_email)