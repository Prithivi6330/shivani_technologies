from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from core.views import register_view, login_view

urlpatterns = [
    # 🔒 Admin Panel
    path('admin/', admin.site.urls),

    # 🏠 Home Page (முதலில் இருக்கட்டும்)
    path('', views.home, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('', views.home, name='home'),
    path('about/', views.about_view, name='about'),
    path('about/', views.about_us, name='about'),
path('services/', views.services, name='services'),
path('contact/', views.contact_us, name='contact'),

    # 📝 Candidate Authentication & Features
    path('register/', views.candidate_register, name='candidate_register'),
    path('login/', views.candidate_login, name='candidate_login'),
    path('otp-verify/', views.otp_verification, name='otp_verification'),
    path('dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('logout/', views.user_logout, name='logout'),

    # 💼 HR Authentication & Panel
    path('hr-login/', views.hr_login_view, name='hr_login'),
    path('hr/register/', views.hr_register, name='hr_register'),
    path('hr/verify-otp/', views.hr_verify_otp, name='hr_verify_otp'),
    path('hr/company-setup/', views.hr_company_setup, name='hr_company_setup'),
    
    # HR Dashboard Panel (ஒரே ஒரு மெயின் URL மட்டும் போதும்)
    path('hr-panel/', views.hr_dashboard, name='hr_dashboard'),
    path('hr-panel/add-job/', views.hr_add_job, name='hr_add_job'),
    path('hr-panel/update/<int:app_id>/<str:action>/', views.update_application_status, name='update_status'),
    path('edit-hr-profile/', views.edit_hr_profile, name='edit_hr_profile'),
    path('update-status/<int:id>/<str:status>/', views.update_status, name='update_status'),
]

# 📂 Media Files configuration
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)