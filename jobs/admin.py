from django.contrib import admin
from django.http import HttpResponse
import csv

from .models import Job, Application


@admin.action(description="Export selected jobs to CSV")
def export_jobs_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="jobs_export.csv"'

    writer = csv.writer(response)

    # Header row – adjust if you add/remove fields later
    writer.writerow(
        [
            "ID",
            "Title",
            "Company",
            "Location",
            "Job Type",
            "Experience Level",
            "Salary Range",
            "Posted At",
            "Is Active",
            "Latitude",
            "Longitude",
            "Description",
            "Requirements",
        ]
    )

    for job in queryset:
        # nice formatting
        posted_at_str = (
            job.posted_at.strftime("%Y-%m-%d %H:%M") if job.posted_at else ""
        )
        is_active_str = "Yes" if job.is_active else "No"

        writer.writerow(
            [
                job.id,
                job.title,
                job.company,
                job.location,
                job.job_type,
                job.experience_level,
                job.salary_range,
                posted_at_str,
                is_active_str,
                job.latitude,
                job.longitude,
                job.description,
                job.requirements,
            ]
        )

    return response


@admin.action(description="Export selected applications to CSV")
def export_applications_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="applications_export.csv"'

    writer = csv.writer(response)

    writer.writerow(
        [
            "ID",
            "Job ID",
            "Job Title",
            "Applicant Username",
            "Applicant Email",
            "Status",
            "Applied At",
            "Application Note",
        ]
    )

    # use select_related to avoid N+1 queries
    for app in queryset.select_related("job", "applicant"):
        applicant = app.applicant
        applied_at_str = (
            app.applied_at.strftime("%Y-%m-%d %H:%M") if app.applied_at else ""
        )

        writer.writerow(
            [
                app.id,
                app.job.id if app.job else "",
                app.job.title if app.job else "",
                getattr(applicant, "username", "") if applicant else "",
                getattr(applicant, "email", "") if applicant else "",
                app.status,
                applied_at_str,
                app.application_note,
            ]
        )

    return response


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "company",
        "location",
        "job_type",
        "experience_level",
        "salary_range",
        "posted_at",
        "is_active",
    ]
    list_filter = [
        "job_type",
        "experience_level",
        "company",
        "location",
        "posted_at",
        "is_active",
    ]
    search_fields = ["title", "company", "location", "description"]
    list_editable = ["is_active"]
    # keep delete_selected and add our export action
    actions = [export_jobs_csv, "delete_selected"]

    fieldsets = [
        (
            "Basic Information",
            {"fields": ["title", "company", "location", "is_active"]},
        ),
        (
            "Job Details",
            {"fields": ["job_type", "experience_level", "salary_range"]},
        ),
        (
            "Description & Requirements",
            {"fields": ["description", "requirements"]},
        ),
        (
            "Location Coordinates (for map)",
            {"fields": ["latitude", "longitude"], "classes": ["collapse"]},
        ),
    ]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["job", "applicant", "applied_at", "status"]
    list_filter = ["status", "applied_at", "job__company"]
    search_fields = ["applicant__username", "job__title", "application_note"]
    list_editable = ["status"]
    readonly_fields = ["applied_at"]
    actions = [export_applications_csv]
