from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Job, Application
from .forms import QuickApplyForm, TraditionalApplyForm



def job_list(request):
    # Get all active jobs initially
    jobs = Job.objects.filter(is_active=True)
    
    # Get filter parameters from GET request
    search_query = request.GET.get('q', '')
    job_type = request.GET.get('job_type', '')
    experience_level = request.GET.get('experience_level', '')
    location_query = request.GET.get('location', '')
    
    # Apply filters
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(requirements__icontains=search_query)
        )
    
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)
    
    if location_query:
        jobs = jobs.filter(location__icontains=location_query)
    
    # Order by most recent
    jobs = jobs.order_by('-posted_at')
    
    # Get unique values for filter dropdowns
    job_types = Job.JOB_TYPE_CHOICES
    experience_levels = Job.EXPERIENCE_LEVEL_CHOICES
    
    # Get unique locations for suggestions
    locations = Job.objects.filter(is_active=True).values_list('location', flat=True).distinct()
    
    context = {
        'jobs': jobs,
        'search_query': search_query,
        'selected_job_type': job_type,
        'selected_experience': experience_level,
        'location_query': location_query,
        'job_types': job_types,
        'experience_levels': experience_levels,
        'locations': locations,
        'results_count': jobs.count()
    }
    return render(request, 'jobs/job_list.html', context)

def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    has_applied = False
    user_application = None
    
    if request.user.is_authenticated:
        has_applied = Application.objects.filter(job=job, applicant=request.user).exists()
        if has_applied:
            user_application = Application.objects.get(job=job, applicant=request.user)
    
    # Get related jobs (same company or similar title)
    related_jobs = Job.objects.filter(
        Q(company=job.company) | Q(title__icontains=job.title.split()[0]),
        is_active=True
    ).exclude(id=job.id).distinct()[:3]
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'user_application': user_application,
        'related_jobs': related_jobs,
    }
    return render(request, 'jobs/job_detail.html', context)

@login_required
def quick_apply(request, job_id):
    """Quick Apply - creates application and redirects to form"""
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Check if already applied
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, 'You have already applied to this job.')
        return redirect('job_detail', job_id=job_id)
    
    # Create application record
    application = Application.objects.create(
        job=job,
        applicant=request.user,
        application_note=""
    )
    
    messages.info(request, 'Please upload your resume to complete your Quick Apply.')
    return redirect('quick_apply_form', job_id=job_id)

@login_required
def quick_apply_form(request, job_id):
    """Form for Quick Apply completion - resume required, message optional"""
    job = get_object_or_404(Job, id=job_id, is_active=True)
    application = get_object_or_404(Application, job=job, applicant=request.user)
    
    if request.method == 'POST':
        form = QuickApplyForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Quick Apply completed for {job.title} at {job.company}!')
            return redirect('job_detail', job_id=job_id)
    else:
        form = QuickApplyForm(instance=application)
    
    context = {
        'job': job,
        'form': form,
        'apply_type': 'quick'
    }
    return render(request, 'jobs/apply_job.html', context)

@login_required
def apply_to_job(request, job_id):
    """Traditional Apply - both resume and message required"""
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Check if user already applied
    has_applied = Application.objects.filter(job=job, applicant=request.user).exists()
    
    if has_applied:
        # If already applied, redirect to update page with QuickApplyForm
        messages.info(request, 'You have already applied to this job. You can update your application.')
        return redirect('quick_apply_form', job_id=job_id)
    
    if request.method == 'POST':
        form = TraditionalApplyForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            
            messages.success(request, f'✅ Application submitted for {job.title} at {job.company}!')
            return redirect('job_detail', job_id=job_id)
    else:
        form = TraditionalApplyForm()
    
    context = {
        'job': job,
        'form': form,
        'has_applied': has_applied,
        'apply_type': 'traditional'
    }
    return render(request, 'jobs/apply_job.html', context)

@login_required
def my_applications(request):
    """View for users to see their applications"""
    applications = Application.objects.filter(applicant=request.user).order_by('-applied_at')
    
    context = {
        'applications': applications,
    }
    return render(request, 'jobs/applications.html', context)

def job_map(request):
    jobs = Job.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    context = {
        'template_data': {
            'title': 'Job Map'
        },
        'jobs': jobs
    }
    return render(request, 'jobs/job_map.html', context)