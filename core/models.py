from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import random
from django.contrib.auth.models import User

# 1. Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('candidate', 'Candidate'),
        ('hr', 'HR'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username
    
    groups = models.ManyToManyField("auth.Group", related_name="core_user_groups", blank=True)
    user_permissions = models.ManyToManyField("auth.Permission", related_name="core_user_permissions", blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

# 2. Base Company Model
class Company(models.Model):
    hr = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Companies"

# 3. Lookup Tables
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Designation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

# 4. Profiles
class HRProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hr_profile')
    phone_number = models.CharField(max_length=15)
    designation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=255, blank=True, null=True) # இதுதான் முக்கியம்!
    is_verified = models.BooleanField(default=False)
    profile_pic = models.ImageField(upload_to='hr_pics/', blank=True, null=True) 
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    def generate_otp(self):
        """OTP உருவாக்கி சேமிக்கும் பங்க்ஷன்"""
        otp = str(random.randint(100000, 999999))
        self.otp = otp
        self.save()
        return otp
        
    def __str__(self):
        return f"HR: {self.user.username}"

class CompanyProfile(models.Model):
    hr = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='profiles')
    company_name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100)
    company_size = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    about = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

# 5. Job Operations
class JobOpening(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_openings')
    title = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    skills = models.ManyToManyField(Skill)
    salary_range = models.CharField(max_length=100)
    experience_required = models.IntegerField(help_text="In Years")
    qualification = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    hr = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.title} - {self.company.name}"

class JobApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, default='Pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    designation = models.CharField(max_length=100) # தேவைப்பட்டால் இதைச் சேர்க்கவும்
    skills = models.TextField()
    address = models.TextField(null=True, blank=True)
    tenth_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    twelfth_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    college_cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"