from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from .models import Job, Application, Message
from .forms import QuickApplyForm, TraditionalApplyForm, JobCreationForm, MessageForm
from django.contrib.auth.models import User
from geopy.geocoders import Nominatim
from math import radians, cos, sin, asin, sqrt

def geocode_zip(zip_code):
    """Return (latitude, longitude) for a ZIP code using OpenStreetMap."""
    url = f"https://nominatim.openstreetmap.org/search?q={zip_code}&format=json&limit=1"
    headers = {"User-Agent": "job_map_app"}  # required by Nominatim
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            print(f"✅ Geocoded {zip_code}: ({lat}, {lon})")  # you can check this in console
            return lat, lon
    except Exception as e:
        print("Error geocoding:", e)
    return None, None

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

def haversine(lat1, lon1, lat2, lon2):
    # convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 3956  # Radius of earth in miles
    return c * r

def job_map(request):
    jobs = Job.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    user_lat, user_lng = None, None
    zip_code = request.GET.get('zip_code')
    radius = request.GET.get('radius')
    
    if zip_code and radius:
        radius = float(radius)
        user_lat, user_lng = geocode_zip(zip_code)

        if user_lat and user_lng:
            jobs = [
                job for job in jobs
                if job.latitude and job.longitude and
                haversine(user_lat, user_lng, job.latitude, job.longitude) <= radius
            ]
        else:
            print("Could not geocode ZIP code")
    context = {"template_data": {"title": "Job Map"}, "jobs": jobs, "user_lat": user_lat, "user_lng": user_lng}
    return render(request, "jobs/job_map.html", context)


@login_required
def job_recommendations(request):
    profile = request.user.profile

    # Safely handle None or empty skills
    raw_skills = profile.skills or ""  # fallback to empty string
    user_skills = [s.strip().lower() for s in raw_skills.split(",") if s.strip()]

    if not user_skills:
        messages.info(request, "You haven't added any skills yet. Update your profile to get recommendations.")
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
            
            # Set the current user as employer
            job.employer = request.user
            
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
    
    # Get jobs posted by this recruiter
    jobs = Job.objects.filter(employer=request.user).order_by('-posted_at')
    
    # Get applications for this recruiter's jobs
    applications = Application.objects.filter(job__employer=request.user).order_by('-applied_at')
    
    # Get recent messages sent by this recruiter
    recent_messages = Message.objects.filter(sender=request.user).order_by('-sent_at')[:5]
    
    # ADD THESE LINES: Get unread messages for notifications
    unread_messages = Message.objects.filter(recipient=request.user, is_read=False)
    unread_count = unread_messages.count()
    
    context = {
        'jobs': jobs,
        'applications': applications,
        'recent_messages': recent_messages,
        'total_jobs': jobs.count(),
        'total_applications': applications.count(),
        'unread_count': unread_count,  # ADD THIS
        'unread_messages': unread_messages[:5],  # ADD THIS for recent unread messages
    }
    return render(request, 'jobs/recruiter_dashboard.html', context)

@login_required
def recruiter_applicants_map(request):

    # Get all applications
    applications = Application.objects.filter(job__employer=request.user).order_by('-applied_at')
    print("applications:", applications)  # Debugging line
    # Collect applicants with valid zip codes
    applicants = []
    for app in applications:
        profile = getattr(app.applicant, 'profile', None)
        if profile and profile.latitude and profile.longitude:
                applicants.append({
                    'username': app.applicant.username,
                    'lat': profile.latitude,
                    'lng': profile.longitude
                })
    print("applicants:", applicants)  # Debugging line
    return render(request, 'jobs/recruiter_applicants_map.html', {
        'applicants': applicants,
    })

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
    
    # Get recent messages
    recent_messages = Message.objects.filter(recipient=request.user).order_by('-sent_at')[:5]
    unread_count = Message.objects.filter(recipient=request.user, is_read=False).count()
    
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
        'recent_messages': recent_messages,
        'unread_count': unread_count,
    }
    return render(request, 'jobs/user_dashboard.html', context)


# ============================================================================
# MESSAGING VIEWS
# ============================================================================

@login_required
def send_message(request, application_id=None):
    """Send a message to a candidate"""
    # Check if user is a recruiter
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'recruiter':
        messages.error(request, 'Only recruiters can send messages.')
        return redirect('user_dashboard')
    
    application = None
    candidate = None
    
    if application_id:
        application = get_object_or_404(Application, id=application_id)
        # Verify the recruiter has access to this application
        if application.job.employer != request.user:
            messages.error(request, 'You do not have permission to message this candidate.')
            return redirect('recruiter_dashboard')
        candidate = application.applicant
    
    # Handle candidate selection from GET parameter
    candidate_id = request.GET.get('candidate_id')
    if candidate_id and not candidate:
        candidate = get_object_or_404(User, id=candidate_id)
        # Verify this candidate applied to recruiter's jobs
        if not Application.objects.filter(applicant=candidate, job__employer=request.user).exists():
            messages.error(request, 'This candidate has not applied to any of your jobs.')
            return redirect('select_candidate')
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            
            # Get candidate from POST or existing context
            candidate_id = request.POST.get('candidate_id')
            if candidate_id:
                candidate = get_object_or_404(User, id=candidate_id)
            
            if candidate:
                message.recipient = candidate
            
            if application:
                message.application = application
                if not message.subject.startswith('Re:'):
                    message.subject = f"Re: Your application for {application.job.title}"
            
            message.save()
            
            recipient_name = message.recipient.get_full_name() or message.recipient.username
            messages.success(request, f'Message sent to {recipient_name}!')
            return redirect('sent_messages')
    else:
        initial = {}
        if application:
            initial = {
                'subject': f"Regarding your application for {application.job.title}",
                'message_type': 'application'
            }
        elif candidate:
            # Get the most recent application for context
            recent_app = Application.objects.filter(
                applicant=candidate, 
                job__employer=request.user
            ).first()
            if recent_app:
                initial = {
                    'subject': f"Regarding your application for {recent_app.job.title}",
                    'message_type': 'application'
                }
            else:
                initial = {
                    'subject': f"Regarding your application",
                    'message_type': 'application'
                }
        form = MessageForm(initial=initial)
    
    context = {
        'form': form,
        'application': application,
        'candidate': candidate,
        'recipient': candidate if candidate else None
    }
    return render(request, 'jobs/send_message.html', context)

@login_required
def select_candidate(request):
    """View for recruiters to select which candidate to message"""
    # Check if user is a recruiter
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'recruiter':
        messages.error(request, 'Only recruiters can send messages.')
        return redirect('user_dashboard')
    
    # Get all unique candidates who applied to this recruiter's jobs
    candidates = User.objects.filter(
        job_applications__job__employer=request.user
    ).distinct()
    
    # Get application counts for each candidate
    candidate_data = []
    for candidate in candidates:
        applications = Application.objects.filter(
            applicant=candidate,
            job__employer=request.user
        )
        candidate_data.append({
            'candidate': candidate,
            'applications': applications,
            'application_count': applications.count()
        })
    
    context = {
        'candidates': candidate_data,
    }
    return render(request, 'jobs/select_candidate.html', context)

@login_required
def inbox(request):
    """View received messages"""
    user_messages = Message.objects.filter(recipient=request.user).order_by('-sent_at')
    unread_count = user_messages.filter(is_read=False).count()
    
    # Mark messages as read when viewing inbox
    user_messages.filter(is_read=False).update(is_read=True)
    
    context = {
        'user_messages': user_messages,  
        'unread_count': unread_count
    }
    return render(request, 'jobs/inbox.html', context)


@login_required
def sent_messages(request):
    """View sent messages"""
    sent_messages = Message.objects.filter(sender=request.user).order_by('-sent_at')
    
    context = {
        'sent_messages': sent_messages
    }
    return render(request, 'jobs/sent_messages.html', context)


@login_required
def message_detail(request, message_id):
    """View a specific message"""
    message = get_object_or_404(Message, id=message_id)
    
    # Verify user has permission to view this message
    if message.recipient != request.user and message.sender != request.user:
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('inbox')
    
    # Mark as read if recipient is viewing
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
    
    context = {
        'message': message
    }
    return render(request, 'jobs/message_detail.html', context)


@login_required
def reply_message(request, message_id):
    """Reply to a message"""
    original_message = get_object_or_404(Message, id=message_id)
    
    if original_message.recipient != request.user:
        messages.error(request, 'You can only reply to messages sent to you.')
        return redirect('inbox')
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = original_message.sender
            message.application = original_message.application
            message.save()
            
            messages.success(request, 'Reply sent successfully!')
            return redirect('inbox')
    else:
        # Pre-fill the form with reply information
        form = MessageForm(initial={
            'subject': f"Re: {original_message.subject}",
            'content': f"\n\n--- Original Message ---\nFrom: {original_message.sender.get_full_name() or original_message.sender.username}\nSent: {original_message.sent_at.strftime('%Y-%m-%d %H:%M')}\n\n{original_message.content}",
            'message_type': 'application'
        })
        # Make subject field read-only
        form.fields['subject'].widget.attrs['readonly'] = True
        form.fields['subject'].widget.attrs['class'] = 'form-control bg-light'
        form.fields['subject'].widget.attrs['style'] = 'cursor: not-allowed;'
    
    context = {
        'form': form,
        'original_message': original_message
    }
    return render(request, 'jobs/reply_message.html', context)


@login_required
def view_application(request, application_id):
    """View application details (for recruiters)"""
    application = get_object_or_404(Application, id=application_id)
    
    # Verify the employer has access to this application
    if application.job.employer != request.user and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to view this application.')
        return redirect('recruiter_dashboard')
    
    # Get messages related to this application
    application_messages = Message.objects.filter(application=application).order_by('sent_at')  # CHANGED variable name
    
    context = {
        'application': application,
        'application_messages': application_messages,  # CHANGED from 'messages'
    }
    return render(request, 'jobs/view_application.html', context)

@login_required
def dashboard(request):
    """Universal dashboard that redirects based on user type"""
    if not hasattr(request.user, 'profile'):
        messages.info(request, 'Please complete your profile setup.')
        return redirect('job_list')
    
    if request.user.profile.user_type == 'recruiter':
        return redirect('recruiter_dashboard')
    else:
        return redirect('user_dashboard')
