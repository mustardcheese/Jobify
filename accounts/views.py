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
from jobs.utils import test_email_connection  # Import the test function


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
            # Create a profile for the new user with the selected user type and email
            user_type = form.cleaned_data.get('user_type', 'user')
            email = form.cleaned_data.get('email', '')
            UserProfile.objects.create(
                user=user, 
                user_type=user_type,
                email=email  # Save the email to profile
            )
            
            # Show success message
            user_type_display = UserProfile.USER_TYPE_CHOICES[int(user_type == 'recruiter')][1]
            messages.success(request, f"Account created successfully! Welcome as a {user_type_display}.")
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
