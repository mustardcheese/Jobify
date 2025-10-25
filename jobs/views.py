from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from .models import Job, Application
from .forms import QuickApplyForm, TraditionalApplyForm, JobCreationForm


def job_list(request):
    # Get all active jobs initially
    jobs = Job.objects.filter(is_active=True)

    # Get filter parameters from GET request
    search_query = request.GET.get("q", "")
    job_type = request.GET.get("job_type", "")
    experience_level = request.GET.get("experience_level", "")
    location_query = request.GET.get("location", "")

    # Apply filters
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query)
            | Q(company__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(requirements__icontains=search_query)
        )

    if job_type:
        jobs = jobs.filter(job_type=job_type)

    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)

    if location_query:
        jobs = jobs.filter(location__icontains=location_query)

    # Order by most recent
    jobs = jobs.order_by("-posted_at")

    # Get unique values for filter dropdowns
    job_types = Job.JOB_TYPE_CHOICES
    experience_levels = Job.EXPERIENCE_LEVEL_CHOICES

    # Get unique locations for suggestions
    locations = (
        Job.objects.filter(is_active=True).values_list("location", flat=True).distinct()
    )

    context = {
        "jobs": jobs,
        "search_query": search_query,
        "selected_job_type": job_type,
        "selected_experience": experience_level,
        "location_query": location_query,
        "job_types": job_types,
        "experience_levels": experience_levels,
        "locations": locations,
        "results_count": jobs.count(),
    }
    return render(request, "jobs/job_list.html", context)


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    has_applied = False
    user_application = None

    if request.user.is_authenticated:
        has_applied = Application.objects.filter(
            job=job, applicant=request.user
        ).exists()
        if has_applied:
            user_application = Application.objects.get(job=job, applicant=request.user)

    # Get related jobs (same company or similar title)
    related_jobs = (
        Job.objects.filter(
            Q(company=job.company) | Q(title__icontains=job.title.split()[0]),
            is_active=True,
        )
        .exclude(id=job.id)
        .distinct()[:3]
    )

    context = {
        "job": job,
        "has_applied": has_applied,
        "user_application": user_application,
        "related_jobs": related_jobs,
    }
    return render(request, "jobs/job_detail.html", context)


@login_required
def quick_apply(request, job_id):
    """Quick Apply - creates application and redirects to form"""
    job = get_object_or_404(Job, id=job_id, is_active=True)

    # Check if already applied
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, "You have already applied to this job.")
        return redirect("job_detail", job_id=job_id)

    # Create application record
    application = Application.objects.create(
        job=job, applicant=request.user, application_note=""
    )

    messages.info(request, "Please upload your resume to complete your Quick Apply.")
    return redirect("quick_apply_form", job_id=job_id)


@login_required
def quick_apply_form(request, job_id):
    """Form for Quick Apply completion - resume required, message optional"""
    job = get_object_or_404(Job, id=job_id, is_active=True)
    application = get_object_or_404(Application, job=job, applicant=request.user)

    if request.method == "POST":
        form = QuickApplyForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"✅ Quick Apply completed for {job.title} at {job.company}!"
            )
            return redirect("job_detail", job_id=job_id)
    else:
        form = QuickApplyForm(instance=application)

    context = {"job": job, "form": form, "apply_type": "quick"}
    return render(request, "jobs/apply_job.html", context)


@login_required
def apply_to_job(request, job_id):
    """Traditional Apply - both resume and message required"""
    job = get_object_or_404(Job, id=job_id, is_active=True)

    # Check if user already applied
    has_applied = Application.objects.filter(job=job, applicant=request.user).exists()

    if has_applied:
        # If already applied, redirect to update page with QuickApplyForm
        messages.info(
            request,
            "You have already applied to this job. You can update your application.",
        )
        return redirect("quick_apply_form", job_id=job_id)

    if request.method == "POST":
        form = TraditionalApplyForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()

            messages.success(
                request, f"✅ Application submitted for {job.title} at {job.company}!"
            )
            return redirect("job_detail", job_id=job_id)
    else:
        form = TraditionalApplyForm()

    context = {
        "job": job,
        "form": form,
        "has_applied": has_applied,
        "apply_type": "traditional",
    }
    return render(request, "jobs/apply_job.html", context)


@login_required
def my_applications(request):
    """View for users to see their applications"""
    applications = Application.objects.filter(applicant=request.user).order_by(
        "-applied_at"
    )

    context = {
        "applications": applications,
    }
    return render(request, "jobs/applications.html", context)


def job_map(request):
    jobs = Job.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)

    context = {"template_data": {"title": "Job Map"}, "jobs": jobs}
    return render(request, "jobs/job_map.html", context)

@login_required
def my_applications(request):
    """View for users to see their applications"""
    applications = Application.objects.filter(applicant=request.user).order_by(
        "-applied_at"
    )

    context = {
        "applications": applications,
    }
    return render(request, "jobs/applications.html", context)


def job_map(request):
    jobs = Job.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)

    context = {"template_data": {"title": "Job Map"}, "jobs": jobs}
    return render(request, "jobs/job_map.html", context)


@login_required
def job_recommendations(request):
    profile = request.user.profile

    # Safely handle None or empty skills
    raw_skills = profile.skills or ""  # fallback to empty string
    user_skills = [s.strip().lower() for s in raw_skills.split(",") if s.strip()]

    if not user_skills:
        messages.info(request, "You haven’t added any skills yet. Update your profile to get recommendations.")
        return render(request, "jobs/recommendations.html", {
            "recommended_jobs": [],
            "user_skills": [],
        })

    # Build query across multiple fields
    query = Q()
    for skill in user_skills:
        query |= (
            Q(title__icontains=skill) |
            Q(description__icontains=skill) |
            Q(requirements__icontains=skill)
        )

    jobs = Job.objects.filter(is_active=True).filter(query).distinct()

    # Rank jobs by number of matched skills
    ranked_jobs = []
    for job in jobs:
        job_text = f"{job.title} {job.description} {job.requirements}".lower()
        match_count = sum(1 for skill in user_skills if skill in job_text)
        if match_count > 0:
            ranked_jobs.append((job, match_count))

    ranked_jobs.sort(key=lambda x: x[1], reverse=True)

    recommended_jobs = []
    for job, count in ranked_jobs:
        job.match_count = count
        recommended_jobs.append(job)

    if not recommended_jobs:
        messages.warning(request, "No job recommendations found. Try adding more skills to your profile.")

    return render(request, "jobs/recommendations.html", {
        "recommended_jobs": recommended_jobs,
        "user_skills": user_skills,
    })


def geocode_location(location_text):
    """
    Geocode a location string to get latitude and longitude coordinates.
    Uses OpenStreetMap Nominatim API (free, no API key required).
    """
    if not location_text or not location_text.strip():
        return None
        
    try:
        # Use OpenStreetMap Nominatim API
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': location_text.strip(),
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'countrycodes': '',  # Allow global search
            'bounded': 0,  # Don't restrict to specific bounds
        }
        headers = {
            'User-Agent': 'Jobify/1.0 (job posting location mapping)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            result = data[0]
            # Validate coordinates
            lat = float(result['lat'])
            lng = float(result['lon'])
            
            # Basic coordinate validation
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return {
                    'latitude': lat,
                    'longitude': lng,
                    'display_name': result.get('display_name', location_text.strip())
                }
            else:
                print(f"Invalid coordinates: lat={lat}, lng={lng}")
                return None
        else:
            print(f"No results found for location: {location_text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"Geocoding timeout for location: {location_text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Geocoding request error for {location_text}: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"Geocoding data parsing error for {location_text}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected geocoding error for {location_text}: {e}")
        return None


@login_required
def create_job(request):
    """View for recruiters to create new job postings with location mapping"""
    # Check if user is a recruiter
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'recruiter':
        messages.error(request, "Access denied. This feature is only available for recruiters.")
        return redirect('job_list')
    if request.method == 'POST':
        form = JobCreationForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            
            # Geocode the location to get coordinates
            location_data = geocode_location(job.location)
            if location_data:
                job.latitude = location_data['latitude']
                job.longitude = location_data['longitude']
                messages.success(request, f"✅ Job created successfully! Location mapped: {location_data['display_name']}")
            else:
                messages.warning(request, "⚠️ Job created but location could not be mapped. You can add coordinates manually in the admin panel.")
            
            job.save()
            return redirect('recruiter_dashboard')
    else:
        form = JobCreationForm()
    
    context = {
        'form': form,
        'title': 'Create New Job Posting'
    }
    return render(request, 'jobs/create_job.html', context)


@login_required
def recruiter_dashboard(request):
    """Dashboard for recruiters to manage their job postings"""
    # Check if user is a recruiter
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'recruiter':
        messages.error(request, "Access denied. This feature is only available for recruiters.")
        return redirect('job_list')
    # Get all jobs (assuming all users can see all jobs for now)
    # In a real app, you'd filter by the recruiter/company
    jobs = Job.objects.all().order_by('-posted_at')
    
    context = {
        'jobs': jobs,
        'total_jobs': jobs.count()
    }
    return render(request, 'jobs/recruiter_dashboard.html', context)




@csrf_exempt
def geocode_ajax(request):
    """AJAX endpoint for geocoding locations"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            location = data.get('location', '')
            
            if location:
                result = geocode_location(location)
                if result:
                    return JsonResponse({
                        'success': True,
                        'latitude': result['latitude'],
                        'longitude': result['longitude'],
                        'display_name': result['display_name']
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Location not found'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No location provided'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def user_dashboard(request):
    """Dashboard for job seekers"""
    # Check if user is a job seeker
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'user':
        messages.error(request, "Access denied. This feature is only available for job seekers.")
        return redirect('recruiter_dashboard')
    
    # Get user's applications
    applications = Application.objects.filter(applicant=request.user).order_by('-applied_at')
    
    # Get job recommendations
    profile = request.user.profile
    raw_skills = profile.skills or ""
    user_skills = [s.strip().lower() for s in raw_skills.split(",") if s.strip()]
    
    recommended_jobs = []
    if user_skills:
        # Build query across multiple fields
        query = Q()
        for skill in user_skills:
            query |= (
                Q(title__icontains=skill) |
                Q(description__icontains=skill) |
                Q(requirements__icontains=skill)
            )
        
        jobs = Job.objects.filter(is_active=True).filter(query).distinct()
        
        # Rank jobs by number of matched skills
        ranked_jobs = []
        for job in jobs:
            job_text = f"{job.title} {job.description} {job.requirements}".lower()
            match_count = sum(1 for skill in user_skills if skill in job_text)
            if match_count > 0:
                ranked_jobs.append((job, match_count))
        
        ranked_jobs.sort(key=lambda x: x[1], reverse=True)
        
        for job, count in ranked_jobs[:6]:  # Limit to 6 recommendations
            job.match_count = count
            recommended_jobs.append(job)
    
    # Get job statistics
    total_jobs = Job.objects.filter(is_active=True).count()
    
    context = {
        'applications': applications,
        'recommended_jobs': recommended_jobs,
        'total_jobs': total_jobs,
    }
    return render(request, 'jobs/user_dashboard.html', context)
