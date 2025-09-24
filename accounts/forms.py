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
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1','password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})

class SimpleProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'experience', 'education', 'skills', 'profile_privacy', 'allow_recruiters_to_contact']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe your work experience...'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your education background...'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List your skills separated by commas...'}),
            'profile_privacy': forms.Select(attrs={'class': 'form-control'}),
            'allow_recruiters_to_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }