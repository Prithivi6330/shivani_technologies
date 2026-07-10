from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Company, Category, Designation, Location, Skill, JobOpening, JobApplication

# ==========================================
# 1. Custom User Admin
# ==========================================
class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("role", "phone_number")}),
    )
    list_display = ["username", "email", "role", "is_staff"]
    list_filter = ["role", "is_staff", "is_superuser"]


# ==========================================
# 2. Advanced Job Application Admin (Bootstrap Styled)
# ==========================================
class JobApplicationAdmin(admin.ModelAdmin):
    # 'status_badge' மூலம் கலர்ஃபுல் மாடர்ன் பேட்ஜ் காட்டப்படும்
    list_display = ('user', 'job', 'phone_number', 'college_cgpa', 'status_badge', 'status', 'applied_at')
    
    # 👈 லிஸ்ட் பேஜிலேயே நேரடியாக ஒரே கிளிக்கில் 'Status'-ஐ மாற்றி கீழே 'Save' செய்யும் வசதி
    list_editable = ['status']
    
    # அட்மின் பேனல் பில்டர் மற்றும் தேடுதல் வசதிகள்
    list_filter = ('status', 'applied_at', 'job__company')
    search_fields = ('user__username', 'job__title', 'phone_number', 'skills')
    ordering = ('-applied_at',)

    # 💥 பல்க் ஆக்ஷன்ஸ் (டிராப்டவுன் மூலம் ஒரே நேரத்தில் பல அப்ளிகேஷன்களை Accept/Reject செய்ய)
    actions = ['bulk_accept', 'bulk_reject']

    @admin.action(description='🟢 Accept selected applications')
    def bulk_accept(self, request, queryset):
        queryset.update(status='Accepted')
        self.message_user(request, f"Selected {queryset.count()} applications have been Accepted successfully!")

    @admin.action(description='🔴 Reject selected applications')
    def bulk_reject(self, request, queryset):
        queryset.update(status='Rejected')
        self.message_user(request, f"Selected {queryset.count()} applications have been Rejected.")

    # ✨ Bootstrap/CSS மாடர்ன் கலர் பேட்ஜ் எஃபெக்ட்:
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',   # Vibrant Yellow
            'accepted': '#198754',  # Success Green
            'rejected': '#dc3545',  # Danger Red
        }
        
        # ஸ்டேட்டஸ் வேல்யூவை எடுத்து கலர் மேட்ச் செய்கிறோம்
        current_status = obj.status.lower() if obj.status else 'pending'
        color = colors.get(current_status, '#6c757d') 
        
        # நீங்க கேட்ட அதே எக்ஸ்ட்ராடினரி கிளாஸி லுக் வித் ஷேடோ எஃபெக்ட்!
        return format_html(
            '<span style="background-color: {}; color: white; padding: 6px 12px; '
            'border-radius: 50px; font-weight: 600; font-size: 11px; text-transform: uppercase; '
            'letter-spacing: 0.5px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);">{}</span>',
            color, obj.status if obj.status else 'PENDING'
        )
    
    status_badge.short_description = 'Live Status'  # அட்மின் டேபிளின் ஹெட்டிங் பெயர்
    status_badge.admin_order_field = 'status'


# ==========================================
# 3. Job Opening Admin (Extra Enhancement)
# ==========================================
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'category', 'location', 'created_at')
    list_filter = ('category', 'location', 'created_at')
    search_fields = ('title', 'company__name')


# Registering Models to Admin Site
admin.site.register(User, CustomUserAdmin)
admin.site.register(Company)
admin.site.register(Category)
admin.site.register(Designation)
admin.site.register(Location)
admin.site.register(Skill)
admin.site.register(JobOpening, JobOpeningAdmin)
admin.site.register(JobApplication, JobApplicationAdmin)