# accounts/forms.py
from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from django import forms
from .models import UserProfile

class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join([f'<div class="alert alert-danger" role="alert">{e}</div>' for e in self]))


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        }),
        help_text="Your contact email address"
    )
    
    user_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Account Type",
        help_text="Choose your account type. This cannot be changed after signup.",
        initial='user'
    )
    
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'email', 'password1','password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})
        
        # Style the user type field
        self.fields['user_type'].widget.attrs.update({'class': 'form-check-input'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']  # Save email to User model
        if commit:
            user.save()
            # FIXED: Safe approach to handle profile creation
            try:
                # Try to get existing profile
                profile = UserProfile.objects.get(user=user)
                # Update existing profile
                profile.user_type = self.cleaned_data['user_type']
                profile.email = self.cleaned_data['email']
                profile.save()
            except UserProfile.DoesNotExist:
                # Create new profile if it doesn't exist
                UserProfile.objects.create(
                    user=user,
                    user_type=self.cleaned_data['user_type'],
                    email=self.cleaned_data['email']
                )
        return user


class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'experience', 'education', 'skills', 'projects', 'profile_privacy', 'allow_recruiters_to_contact', 'latitude', 'longitude', 'city']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe your work experience...'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your education background...'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List your skills separated by commas...'}),
            'projects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List your projects separated by commas...'}),
            'profile_privacy': forms.Select(attrs={'class': 'form-control'}),
            'allow_recruiters_to_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your city...'}),
        }

class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['email', 'bio', 'experience', 'education', 'skills']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.contact@company.com'
            }),
            'bio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name...'}),
            'experience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your company name...'}),
            'education': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your job title or position...'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your company and what you do...'}),
        }
        labels = {
            'email': 'Contact Email',
        }
        help_texts = {
            'email': 'Your public contact email address.',
        }


# NEW: Email setup form for recruiters
class RecruiterEmailForm(forms.ModelForm):
    email_host_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Gmail App Password',
            'render_value': True
        }),
        help_text="Use a Gmail App Password, not your regular password"
    )
    
    class Meta:
        model = UserProfile
        fields = ['email_host_user', 'email_host_password']
        widgets = {
            'email_host_user': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your-email@gmail.com'
            }),
        }
        labels = {
            'email_host_user': 'Gmail Address',
            'email_host_password': 'App Password',
        }
        help_texts = {
            'email_host_user': 'Your Gmail address that will be used to send emails to candidates.',
        }
    
    def clean_email_host_user(self):
        email = self.cleaned_data['email_host_user']
        # Basic email validation
        if email and not email.endswith('@gmail.com'):
            raise forms.ValidationError("Currently only Gmail accounts are supported.")
        return email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        # Set email as configured after successful save
        profile.email_configured = True
        if commit:
            profile.save()
        return profile

# Keep the old name for backward compatibility
SimpleProfileForm = JobSeekerProfileForm
