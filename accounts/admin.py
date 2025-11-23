from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile
from django.utils.html import format_html

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = [
        'user_type', 'email', 'bio', 'experience', 'education', 'skills', 'projects',
        'profile_privacy', 'allow_recruiters_to_contact', 'city', 'latitude', 'longitude',
        'email_host_user', 'email_configured'
    ]
    readonly_fields = ['created_at', 'updated_at']

class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_user_type', 'get_privacy_status', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined', 'profile__user_type']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')
    
    def get_user_type(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_user_type_display()
        return "No Profile"
    get_user_type.short_description = 'Type'
    get_user_type.admin_order_field = 'profile__user_type'
    
    def get_privacy_status(self, obj):
        if hasattr(obj, 'profile'):
            privacy = obj.profile.profile_privacy
            color_map = {
                'public': 'green',
                'private': 'blue'
            }
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color_map.get(privacy, 'black'),
                obj.profile.get_profile_privacy_display()
            )
        return format_html('<span style="color: red; font-weight: bold;">No Profile</span>')
    get_privacy_status.short_description = 'Privacy'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'get_user_type', 'get_privacy', 'get_city', 'email_configured', 'created_at']
    list_filter = ['user_type', 'profile_privacy', 'email_configured', 'created_at']
    search_fields = ['user__username', 'user__email', 'city', 'skills']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'user_type', 'email')
        }),
        ('Professional Information', {
            'fields': ('bio', 'experience', 'education', 'skills', 'projects')
        }),
        ('Privacy & Contact Settings', {
            'fields': ('profile_privacy', 'allow_recruiters_to_contact', 'city', 'latitude', 'longitude')
        }),
        ('Email Configuration (Recruiters)', {
            'fields': ('email_host_user', 'email_configured'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_info(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    user_info.short_description = 'User'
    user_info.admin_order_field = 'user__username'
    
    def get_user_type(self, obj):
        return obj.get_user_type_display()
    get_user_type.short_description = 'Type'
    get_user_type.admin_order_field = 'user_type'
    
    def get_privacy(self, obj):
        color_map = {
            'public': 'green',
            'private': 'blue'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color_map.get(obj.profile_privacy, 'black'),
            obj.get_profile_privacy_display()
        )
    get_privacy.short_description = 'Privacy'
    get_privacy.admin_order_field = 'profile_privacy'
    
    def get_city(self, obj):
        return obj.city if obj.city else "—"
    get_city.short_description = 'City'
    get_city.admin_order_field = 'city'