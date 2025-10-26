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
    user_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Account Type",
        help_text="Choose your account type. This cannot be changed after signup.",
        initial='user'
    )
    
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1','password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})
        
        # Style the user type field
        self.fields['user_type'].widget.attrs.update({'class': 'form-check-input'})

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'experience', 'education', 'skills', 'profile_privacy', 'allow_recruiters_to_contact', 'latitude', 'longitude']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe your work experience...'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your education background...'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List your skills separated by commas...'}),
            'profile_privacy': forms.Select(attrs={'class': 'form-control'}),
            'allow_recruiters_to_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'latitude': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your latitude...'}),
            'longitude': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your longitude...'}),
        }

class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'experience', 'education', 'skills']
        widgets = {
            'bio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name...'}),
            'experience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your company name...'}),
            'education': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your job title or position...'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your company and what you do...'}),
        }

# Keep the old name for backward compatibility
SimpleProfileForm = JobSeekerProfileForm