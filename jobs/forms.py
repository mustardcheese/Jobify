from django import forms
from .models import Application

class QuickApplyForm(forms.ModelForm):
    """Form for Quick Apply - resume required, message optional"""
    class Meta:
        model = Application
        fields = ['application_note', 'resume']
        widgets = {
            'application_note': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Optional: Add a quick note to stand out...',
                'class': 'form-control'
            }),
        }
        labels = {
            'application_note': 'Quick Note (Optional)',
            'resume': 'Upload Resume *'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resume'].required = True
        self.fields['application_note'].required = False

class TraditionalApplyForm(forms.ModelForm):
    """Form for Traditional Apply - both resume and message required"""
    class Meta:
        model = Application
        fields = ['application_note', 'resume']
        widgets = {
            'application_note': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Why are you interested in this position? What makes you a good fit?',
                'class': 'form-control'
            }),
        }
        labels = {
            'application_note': 'Personalized Message *',
            'resume': 'Upload Resume *'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resume'].required = True
        self.fields['application_note'].required = True