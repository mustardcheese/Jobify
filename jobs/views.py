from django.shortcuts import render
from .models import Job

def job_list(request):
    jobs = Job.objects.all()
    return render(request, 'jobs/job_list.html', {'jobs': jobs})

def job_map(request):
    jobs = Job.objects.all()
    return render(request, 'jobs/job_map.html', {'jobs': jobs})