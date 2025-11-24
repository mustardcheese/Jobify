from django.shortcuts import render
from .forms import CustomUserCreationForm, CustomErrorList, SimpleProfileForm, JobSeekerProfileForm, RecruiterProfileForm, RecruiterEmailForm
from django.contrib.auth import login as auth_login, authenticate
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from jobs.models import Application
from jobs.utils import test_email_connection
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import SavedCandidateSearch, CandidateMatch


def login(request):
    template_data = {}
    template_data["title"] = "Login"
    if request.method == "GET":
        return render(request, "accounts/login.html", {"template_data": template_data})

    elif request.method == "POST":
        user = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )

        if user is None:
            template_data["error"] = "The username or password is incorrect."
            return render(
                request, "accounts/login.html", {"template_data": template_data}
            )

        else:
            auth_login(request, user)
            # Redirect to appropriate dashboard based on user type
            if hasattr(user, 'profile') and user.profile.user_type == 'recruiter':
                return redirect("recruiter_dashboard")
            else:
                return redirect("user_dashboard")


def signup(request):
    template_data = {}
    template_data["title"] = "Sign Up"

    if request.method == "GET":
        template_data["form"] = CustomUserCreationForm()
        return render(request, "accounts/signup.html", {"template_data": template_data})

    elif request.method == "POST":
        form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)

        if form.is_valid():
            user = form.save()
            # The signal will automatically create the UserProfile
            # Just update the profile with additional fields if needed
            try:
                profile = user.profile
                profile.user_type = form.cleaned_data.get('user_type', 'user')
                profile.email = form.cleaned_data.get('email', '')
                profile.save()
            except UserProfile.DoesNotExist:
                # Fallback: create profile if signal didn't work
                UserProfile.objects.create(
                    user=user, 
                    user_type=form.cleaned_data.get('user_type', 'user'),
                    email=form.cleaned_data.get('email', '')
                )
            
            # Show success message
            user_type = form.cleaned_data.get('user_type', 'user')
            user_type_display = dict(UserProfile.USER_TYPE_CHOICES).get(user_type, 'User')
            messages.success(request, f"Account created successfully! Welcome as a {user_type_display}. Please log in to continue.")
            
            # Redirect to login page instead of auto-login
            return redirect("accounts.login")

        else:
            template_data["form"] = form
            return render(
                request, "accounts/signup.html", {"template_data": template_data}
            )

@login_required
def logout(request):
    auth_logout(request)
    return redirect("home.index")

def update_matches_for_user(user):
    """Recompute ALL recruiter saved searches whenever a job seeker updates profile."""

    profile = user.profile
    skills = profile.skills.lower() if profile.skills else ""
    projects = profile.projects.lower() if profile.projects else ""
    city = profile.city.lower() if profile.city else ""

    # Remove old matches for this candidate
    CandidateMatch.objects.filter(candidate=user).delete()

    saved_searches = SavedCandidateSearch.objects.all()

    for s in saved_searches:
        # Skip searches created by the candidate themself
        if s.recruiter == user:
            continue

        skill_ok = (not s.skill) or (s.skill.lower() in skills)
        project_ok = (not s.project) or (s.project.lower() in projects)
        city_ok = (not s.city) or (s.city.lower() == city)

        if skill_ok and project_ok and city_ok:
            CandidateMatch.objects.create(
                search=s,
                candidate=user,
                seen=False
            )

@login_required
def profile(request):
    """Simple profile page with text boxes and privacy controls"""
    template_data = {}
    template_data["title"] = "Profile"

    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    template_data["profile"] = profile
    
    # Use appropriate form based on user type
    if request.user.profile.user_type == 'recruiter':
        form = RecruiterProfileForm(instance=profile)
    else:
        form = JobSeekerProfileForm(instance=profile)
    
    template_data["form"] = form

    return render(request, "accounts/profile.html", {"template_data": template_data})


@login_required
def save_profile(request):
    """Save profile information"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Use appropriate form based on user type
        if request.user.profile.user_type == 'recruiter':
            form = RecruiterProfileForm(request.POST, instance=profile)
        else:
            form = JobSeekerProfileForm(request.POST, instance=profile)
            
        if form.is_valid():
            form.save()
            if request.user.profile.user_type == "user":
                update_matches_for_user(request.user)
            messages.success(request, "Profile saved successfully!")
            return redirect("accounts.profile")
        else:
            messages.error(request, "Please correct the errors below.")

    return redirect("accounts.profile")


@login_required
def user_applications(request):
    applications = Application.objects.filter(applicant=request.user)
    context = {"applications": applications}
    return render(request, "accounts/applications.html", context)


# NEW: Email setup view for recruiters
@login_required
def setup_recruiter_email(request):
    # Use the regular UserProfile, not a separate RecruiterProfile
    try:
        profile = request.user.profile
        # Check if user is actually a recruiter
        if profile.user_type != 'recruiter':
            messages.error(request, "This feature is only available for recruiters.")
            return redirect('user_dashboard')
            
    except UserProfile.DoesNotExist:
        messages.error(request, "Profile not found.")
        return redirect('user_dashboard')

    if request.method == 'POST':
        # Use RecruiterEmailForm (the one you imported) instead of RecruiterEmailSetupForm
        form = RecruiterEmailForm(request.POST, instance=profile)
        if form.is_valid():
            # Use Gmail SMTP settings
            email_host = 'smtp.gmail.com'
            email_port = 587
            email_host_user = form.cleaned_data['email_host_user']
            email_host_password = form.cleaned_data['email_host_password']
            use_tls = True
            
            # Test the connection
            success, message = test_email_connection(
                email_host, email_port, email_host_user, email_host_password, use_tls
            )
            
            if success:
                # Save the form and update profile with SMTP settings
                email_settings = form.save(commit=False)
                email_settings.email_host = email_host
                email_settings.email_port = email_port
                email_settings.email_use_tls = use_tls
                email_settings.email_configured = True  # FIXED: Use the new field name
                email_settings.save()
                
                messages.success(request, message)
                return redirect('recruiter_dashboard')
            else:
                messages.error(request, f"Email configuration failed: {message}")
    else:
        form = RecruiterEmailForm(instance=profile)

    context = {
        'form': form,
        'profile': profile
    }
    return render(request, 'accounts/setup_recruiter_email.html', context)

@login_required
def search_candidates(request):
    if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'recruiter':
        messages.error(request, "You must be a recruiter to access this page.")
        return redirect('home.index')

    # Get search inputs
    skill = request.GET.get('skill', '')
    city = request.GET.get('city', '')
    project = request.GET.get('project', '')

    # Normalize empty values for matching saved searches
    normalized_skill = skill.strip() or ""
    normalized_city = city.strip() or ""
    normalized_project = project.strip() or ""

    # Find saved search with EXACT same criteria
    saved_searches = SavedCandidateSearch.objects.filter(
        recruiter=request.user,
        skill=normalized_skill,
        city=normalized_city,
        project=normalized_project,
    )

    # If matched saved search exists, reset matches for that search only
    if saved_searches.exists():
        CandidateMatch.objects.filter(
            search__in=saved_searches,
            seen=False
        ).update(seen=True)

    # Filter candidates
    candidates = UserProfile.objects.filter(user_type='user', profile_privacy='public')

    if skill:
        candidates = candidates.filter(skills__icontains=skill)
    if city:
        candidates = candidates.filter(city__icontains=city)
    if project:
        candidates = candidates.filter(projects__icontains=project)

    context = {
        'template_data': {
            'title': 'Search Candidates',
            'candidates': candidates,
            'skill': skill,
            'city': city,
            'project': project,
        }
    }
    return render(request, 'accounts/search_candidates.html', context)

@login_required
def save_candidate_search(request):
    """Save a recruiter’s candidate search."""
    user = request.user

    # Only recruiters can save searches
    if not hasattr(user, "profile") or user.profile.user_type != "recruiter":
        messages.error(request, "Only recruiters can save searches.")
        return redirect("search_candidates")

    # Get search parameters from URL
    skill = request.GET.get("skill") or ""
    city = request.GET.get("city") or ""
    project = request.GET.get("project") or ""

    # At least one field must be filled
    if not (skill or city or project):
        messages.warning(request, "You must enter at least one search field before saving.")
        return redirect("search_candidates")

    # Save the search
    SavedCandidateSearch.objects.create(
        recruiter=user,
        skill=skill.strip(),
        city=city.strip(),
        project=project.strip(),
    )

    messages.success(request, "Your search has been saved successfully!")
    return redirect("search_candidates")

@login_required
def saved_candidate_searches(request):
    # Only recruiters
    if (
        not hasattr(request.user, "profile")
        or request.user.profile.user_type != "recruiter"
    ):
        messages.error(request, "Access denied. Recruiter-only feature.")
        return redirect("user_dashboard")

    searches = SavedCandidateSearch.objects.filter(
        recruiter=request.user
    ).order_by("-created_at")

    # Reset the match counter by marking all unseen matches as seen
    from accounts.models import CandidateMatch
    CandidateMatch.objects.filter(
        search__recruiter=request.user,
        seen=False
    ).update(seen=True)

    return render(request, "accounts/saved_candidate_searches.html", {
        "searches": searches
    })

@login_required
def delete_candidate_search(request, search_id):
    search = get_object_or_404(SavedCandidateSearch, id=search_id, recruiter=request.user)
    search.delete()
    messages.success(request, "Saved search deleted.")
    return redirect("saved_candidate_searches")
