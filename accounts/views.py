from django.shortcuts import render
from .forms import CustomUserCreationForm, CustomErrorList, SimpleProfileForm, JobSeekerProfileForm, RecruiterProfileForm
from django.contrib.auth import login as auth_login, authenticate
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from jobs.models import Application


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
            # Create a profile for the new user with the selected user type
            user_type = form.cleaned_data.get('user_type', 'user')
            UserProfile.objects.create(user=user, user_type=user_type)
            
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
