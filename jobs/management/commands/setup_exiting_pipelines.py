from django.core.management.base import BaseCommand
from jobs.models import Job, Application

class Command(BaseCommand):
    help = 'Setup pipeline stages for existing jobs and applications'
    
    def handle(self, *args, **options):
        # Create pipeline stages for existing jobs without stages
        jobs_without_stages = Job.objects.filter(pipeline_stages__isnull=True)
        
        for job in jobs_without_stages:
            job.create_default_pipeline_stages()
            self.stdout.write(
                self.style.SUCCESS(f'Created pipeline stages for: {job.title}')
            )
        
        # Create pipeline entries for existing applications without pipelines
        applications_without_pipeline = Application.objects.filter(pipeline__isnull=True)
        
        for application in applications_without_pipeline:
            application.create_pipeline_entry()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created pipeline entries for {applications_without_pipeline.count()} applications'
            )
        )