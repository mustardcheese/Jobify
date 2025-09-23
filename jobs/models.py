from django.db import models
from django.db import models

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)   # for map
    longitude = models.FloatField(null=True, blank=True)  # for map
    description = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"
