from django import forms
from .models import Application, Job


class QuickApplyForm(forms.ModelForm):
    """Form for Quick Apply - resume required, message optional"""

    class Meta:
        model = Application
        fields = ["application_note", "resume"]
        widgets = {
            "application_note": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional: Add a quick note to stand out...",
                    "class": "form-control",
                }
            ),
        }
        labels = {
            "application_note": "Quick Note (Optional)",
            "resume": "Upload Resume *",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resume"].required = True
        self.fields["application_note"].required = False


class TraditionalApplyForm(forms.ModelForm):
    """Form for Traditional Apply - both resume and message required"""

    class Meta:
        model = Application
        fields = ["application_note", "resume"]
        widgets = {
            "application_note": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Why are you interested in this position? What makes you a good fit?",
                    "class": "form-control",
                }
            ),
        }
        labels = {
            "application_note": "Personalized Message *",
            "resume": "Upload Resume *",
        }


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resume"].required = True
        self.fields["application_note"].required = True


class JobCreationForm(forms.ModelForm):
    """Form for recruiters to create job postings with location mapping"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'company', 'location', 'description', 'requirements',
            'salary_range', 'job_type', 'experience_level', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Senior Software Engineer'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Tech Corp Inc.'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., San Francisco, CA or 123 Main St, New York, NY',
                'id': 'location-input'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Describe the role, responsibilities, and what makes this opportunity special...'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'List the required skills, experience, and qualifications...'
            }),
            'salary_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., $80,000 - $120,000'
            }),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Job Title *',
            'company': 'Company Name *',
            'location': 'Office Location *',
            'description': 'Job Description *',
            'requirements': 'Requirements',
            'salary_range': 'Salary Range *',
            'job_type': 'Job Type',
            'experience_level': 'Experience Level',
            'is_active': 'Active Job Posting'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['company'].required = True
        self.fields['location'].required = True
        self.fields['description'].required = True
        self.fields['requirements'].required = False
        self.fields['salary_range'].required = True

    def clean_location(self):
        location = self.cleaned_data.get('location')
        if location:
            # Basic validation - ensure location is not too short
            if len(location.strip()) < 3:
                raise forms.ValidationError("Location must be at least 3 characters long.")
            # Check for common invalid inputs
            if location.strip().lower() in ['remote', 'work from home', 'wfh']:
                # Allow remote work but suggest adding city
                pass
        return location

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 2:
            raise forms.ValidationError("Job title must be at least 2 characters long.")
        return title

    def clean_company(self):
        company = self.cleaned_data.get('company')
        if company and len(company.strip()) < 2:
            raise forms.ValidationError("Company name must be at least 2 characters long.")
        return company
