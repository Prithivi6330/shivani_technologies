import random

from django.conf import settings
from django.contrib import messages
from django.contrib import auth
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404

from .models import JobOpening, Category, Location, Skill, Designation, JobApplication
from .models import CompanyProfile
from core.models import Company  # FIX: single canonical import, dropped the duplicate local one
from .forms import (
    HRRegistrationForm, CompanyProfileForm, JobOpeningForm, CandidateRegistrationForm,
)
from .models import HRProfile
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from .models import CompanyProfile, Company
from .forms import CompanyProfileForm


User = get_user_model()


# ======================================================================
# CANDIDATE SIDE
# ======================================================================

def home(request):
    jobs = JobOpening.objects.all().order_by('-created_at')
    context = {'jobs': jobs}
    return render(request, 'core/home.html', {'jobs': jobs})

from django.shortcuts import render

def about_us(request):
    return render(request, 'core/about.html')

def services(request):
    data = {
        'services_list': [
            {'title': 'Web Development', 'desc': 'Custom modern websites.'},
            {'title': 'Digital Marketing', 'desc': 'Boost your online presence.'},
            {'title': 'IT Consulting', 'desc': 'Expert business solutions.'},
        ]
    }
    return render(request, 'core/services.html', data)

def contact_us(request):
    return render(request, 'core/contact.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        # யூசரை உருவாக்குறோம்
        user = User.objects.create_user(username=username, email=email, password=password)
        user.role = role  # ரோலை இங்கே செட் பண்றோம்
        user.save()
        
        return redirect('login') # லாகின் பேஜுக்கு கூட்டிட்டு போகும்
        
    return render(request, 'core/register.html')
   

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # ரோல்-ஐ பொறுத்து டைரக்ட் செய்தல்
            if user.role == 'admin': return redirect('admin_dashboard')
            elif user.role == 'hr': return redirect('hr_dashboard')
            else: return redirect('candidate_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def candidate_register(request):
    if request.user.is_authenticated:
        return redirect('candidate_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        context = {'username': username, 'email': email}

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists! Try another one.")
            return render(request, 'core/register.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, 'core/register.html', context)

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Registration successful! Please login.")
        return redirect('candidate_login')

    return render(request, 'core/register.html')


def candidate_login(request):
    if request.user.is_authenticated:
        return redirect('candidate_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            otp = random.randint(100000, 999999)
            request.session['otp'] = otp
            request.session['user_id'] = user.id

            try:
                send_mail(
                    "Your Login OTP",
                    f"Your OTP is {otp}. Do not share this with anyone.",
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
                return redirect('otp_verification')
            except Exception as e:
                messages.error(request, "Error sending OTP email. Please try again later.")
                print(f"SMTP Error: {e}")
        else:
            messages.error(request, "Invalid username or password!")

    return render(request, 'core/login.html')


def otp_verification(request):
    if request.method == 'POST':
        otp_full = ''.join(request.POST.get(f'otp_{i}', '') for i in range(1, 7))

        if not otp_full.isdigit():
            messages.error(request, "Please enter a valid 6-digit OTP!")
            return render(request, 'core/otp_verify.html')

        saved_otp = request.session.get('otp')
        user_id = request.session.get('user_id')

        if saved_otp and int(otp_full) == int(saved_otp):
            try:
                user = User.objects.get(id=user_id)
                login(request, user)
                request.session.pop('otp', None)
                request.session.pop('user_id', None)
                return redirect('candidate_dashboard')
            except User.DoesNotExist:
                messages.error(request, "User does not exist!")
        else:
            messages.error(request, "Invalid OTP! Please try again.")

    return render(request, 'core/otp_verify.html')


@login_required(login_url='candidate_login')
def candidate_dashboard(request):
    jobs = JobOpening.objects.all().order_by('-created_at')

    category_id = request.GET.get('category')
    location_id = request.GET.get('location')
    designation_id = request.GET.get('designation')
    skill_id = request.GET.get('skill')
    max_salary = request.GET.get('salary')
    min_experience = request.GET.get('experience')

    if category_id:
        jobs = jobs.filter(category_id=category_id)
    if location_id:
        jobs = jobs.filter(location_id=location_id)
    if designation_id:
        jobs = jobs.filter(designation_id=designation_id)
    if skill_id:
        jobs = jobs.filter(skills__id=skill_id)
    if max_salary:
        jobs = jobs.filter(salary_range__icontains=max_salary)
    if min_experience:
        jobs = jobs.filter(experience_required__icontains=min_experience)

    context = {
        'jobs': jobs.distinct(),
        'categories': Category.objects.all(),
        'locations': Location.objects.all(),
        'designations': Designation.objects.all(),
        'skills': Skill.objects.all(),
    }
    return render(request, 'core/dashboard.html', context)


@login_required(login_url='candidate_login')
def apply_job(request, job_id):
    job = get_object_or_404(JobOpening, id=job_id)
    already_applied = JobApplication.objects.filter(user=request.user, job=job).exists()

    if already_applied:
        messages.warning(request, f"You have already applied for {job.title}!")
        return redirect('candidate_dashboard')

    if request.method == "POST":
        phone = request.POST.get('phone_number')
        address = request.POST.get('address')
        designation = request.POST.get('designation')
        skills = request.POST.get('skills')
        tenth = request.POST.get('tenth_percentage')
        twelfth = request.POST.get('twelfth_percentage')
        cgpa = request.POST.get('college_cgpa')
        resume_file = request.FILES.get('resume')

        JobApplication.objects.create(
            user=request.user,
            job=job,
            phone_number=phone,
            address=address,
            designation=designation,
            skills=skills,
            tenth_percentage=tenth,
            twelfth_percentage=twelfth,
            college_cgpa=cgpa,
            resume=resume_file,
        )

        subject = f"Application Received: {job.title} at {job.company.name}"
        message = f"""Dear {request.user.username},

Thank you for applying for the position of {job.title} at {job.company.name}.

We have received your application along with your education and resume details successfully.

Best Regards,
HR Team,
Shivani Technologies"""
        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [request.user.email], fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}")

        messages.success(request, f"Successfully applied for {job.title}! Check your email.")
        return redirect('my_applications')

    return render(request, 'apply_form.html', {'job': job})


@login_required(login_url='candidate_login')
def my_applications(request):
    applications = JobApplication.objects.filter(user=request.user).order_by('-id')
    return render(request, 'my_applications.html', {'applications': applications})


def user_logout(request):
    logout(request)
    return redirect('candidate_login')


# ======================================================================
# HR / EMPLOYER SIDE
# ======================================================================

def hr_register(request):
    if request.method == 'POST':
        form = HRRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # User உருவாக்கவும்
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password')
                user = User.objects.create_user(username=username, email=email, password=password)
                user.is_active = False
                user.save()

                # Profile உருவாக்கவும்
                hr_profile = HRProfile.objects.create(
                    user=user,
                    phone_number=form.cleaned_data.get('phone_number'),
                    designation=form.cleaned_data.get('designation'),
                    qualification=form.cleaned_data.get('qualification'),
                    profile_pic=request.FILES.get('profile_pic')
                )

                # OTP அனுப்பவும்
                otp = str(random.randint(100000, 999999))
                hr_profile.otp = otp
                hr_profile.save()
                send_mail("OTP", f"Your OTP: {otp}", settings.EMAIL_HOST_USER, [user.email])
                
                request.session['verify_user_id'] = user.id
                return redirect('hr_verify_otp')
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            print("Form Errors:", form.errors)
    else:
        form = HRRegistrationForm()
    return render(request, 'core/hr_register.html', {'form': form})


def hr_verify_otp(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('hr_register')

    if request.method == 'POST':
        input_otp = request.POST.get('otp')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect('hr_register')

        if hasattr(user, 'hr_profile'):
            hr_profile = user.hr_profile
            if hr_profile.otp == input_otp:
                hr_profile.is_verified = True
                hr_profile.otp = None
                hr_profile.save()

                user.is_active = True
                user.save()

                login(request, user)
                request.session.pop('verify_user_id', None)  # FIX #5: clear stale session key
                return redirect('hr_company_setup')
            else:
                messages.error(request, "Invalid OTP!")
        else:
            messages.error(request, "HR profile missing. Please contact Admin.")
            return redirect('hr_register')

    return render(request, 'core/hr_verify_otp.html')


def hr_login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'hr_profile'):
            return redirect('hr_dashboard')
        auth.logout(request)

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # FIX #3: authenticate() silently rejects inactive users, so we can never
        # tell "wrong password" apart from "not yet OTP-verified" that way.
        # Look the user up manually first so we can give the right message.
        try:
            candidate_user = User.objects.get(username=username)
        except User.DoesNotExist:
            candidate_user = None

        if candidate_user is None or not candidate_user.check_password(password):
            messages.error(request, "Invalid Username or Password!")
        elif not hasattr(candidate_user, 'hr_profile'):
            messages.error(request, "Access Denied: This account is not registered as an HR!")
        elif not candidate_user.is_active:
            messages.warning(request, "Please verify your email/OTP first!")
        else:
            user = authenticate(request, username=username, password=password)
            login(request, user)
            return redirect('hr_dashboard')

    return render(request, 'core/hr_login.html')


@login_required
def hr_company_setup(request):
    # 1. ஆரம்பத்திலேயே வேரியபிள்களை செட் பண்ணுங்க
    company_profile = None
    form = None
    
    try:
        company_profile = CompanyProfile.objects.get(hr=request.user)
    except CompanyProfile.DoesNotExist:
        company_profile = None

    if request.method == 'POST':
        form = CompanyProfileForm(request.POST, request.FILES, instance=company_profile)
        if form.is_valid():
            company_obj = form.save(commit=False)
            company_obj.hr = request.user
            
            # கம்பெனி ஆப்ஜெக்ட்டை கையாளுதல்
            try:
                comp_obj = Company.objects.get(hr=request.user)
            except Company.DoesNotExist:
                comp_obj = Company.objects.create(
                    hr=request.user,
                    name=company_obj.company_name,
                    email=request.user.email,
                    phone='0000000000',
                    address='Not provided'
                )
            
            company_obj.company = comp_obj
            company_obj.save()
            messages.success(request, "Company details saved successfully!")
            return redirect('hr_dashboard')
            
    else:
        # GET மெத்தடில் ஃபார்ம் உருவாக்குதல்
        form = CompanyProfileForm(instance=company_profile)

    # 2. கடைசியில் இந்த render வரியில் எரர் வராது, ஏன்னா form இப்போ கண்டிப்பா இருக்கும்
    return render(request, 'core/hr_company_setup.html', {'form': form})


@login_required(login_url='hr_login')
def hr_dashboard(request):
    # FIX #1: this view used to be defined twice; the superuser-vs-HR filtering
    # and the stat counts from the first definition were silently discarded
    # because the second definition below overwrote it. Merged into one view.
    if request.user.is_superuser:
        my_companies = Company.objects.all()
        all_applications = JobApplication.objects.all().order_by('-id')
    else:
        my_companies = Company.objects.filter(hr=request.user)
        if not my_companies.exists():
            messages.error(request, "You are not assigned to any company HR profile.")
            return redirect('home')
        all_applications = JobApplication.objects.filter(job__company__in=my_companies).order_by('-id')

    context = {
        'applications': all_applications,
        'companies': my_companies,
        'total': all_applications.count(),
        'accepted': all_applications.filter(status='Accepted').count(),
        'pending': all_applications.filter(status='Pending').count(),
        'rejected': all_applications.filter(status='Rejected').count(),
    }
    return render(request, 'core/hr_dashboard.html', context)


@login_required
def hr_add_job(request):
    # 1. HR-க்கான கம்பெனியை நேரடியாக கண்டறியவும்
    try:
        company = Company.objects.get(hr=request.user)
    except Company.DoesNotExist:
        messages.error(request, "Please set up your company profile first.")
        return redirect('hr_company_setup')

    # 2. POST மெத்தட் மற்றும் ஃபார்ம் கையாளுதல்
    if request.method == 'POST':
        form = JobOpeningForm(request.POST)
        if form.is_valid():
            try:
                job = form.save(commit=False)
                job.company = company  # கம்பெனியை இணைக்கவும்
                job.save()
                form.save_m2m()  # மல்டி-செலக்ட் (Skills) சேவ் செய்ய அவசியம்
                
                messages.success(request, "New job opening posted successfully!")
                return redirect('hr_dashboard') # இதுதான் உங்களை அடுத்த பக்கத்திற்கு கொண்டு செல்லும்
            except Exception as e:
                messages.error(request, f"Error saving job: {e}")
        else:
            # ஃபார்மில் ஏதாவது தவறு இருந்தால் அதை கன்சோலில் பார்க்கவும்
            print(form.errors)
            messages.warning(request, "Please check the form for errors.")
    else:
        form = JobOpeningForm()

    # 3. கச்சிதமான ரெண்டரிங் (எந்த கூடுதல் குறியீடுகளும் இல்லாமல்)
    return render(request, 'core/hr_add_job.html', {
        'form': form,
        'company_name': company.name,
    })


@login_required
def update_application_status(request, app_id, action):
    # FIX #7: merged with the old unprotected `update_status` view, which had
    # no login_required, no permission check, and used .get() instead of
    # get_object_or_404 (a bad id used to throw a raw 500 error).
    if not (request.user.is_superuser or request.user.is_staff):
        return redirect('home')

    application = get_object_or_404(JobApplication, id=app_id)

    if action == 'accept':
        application.status = 'Accepted'
    elif action == 'reject':
        application.status = 'Rejected'
    else:
        messages.error(request, "Unknown action.")
        return redirect('hr_dashboard')

    application.save()

    # The original comment claimed an email "automatically" goes out on save —
    # nothing in the codebase actually did that, so it's implemented here.
    try:
        send_mail(
            f"Your application status: {application.status}",
            f"Dear {application.user.username},\n\n"
            f"Your application for {application.job.title} has been {application.status.lower()}.\n\n"
            f"Best Regards,\nHR Team, Shivani Technologies",
            settings.EMAIL_HOST_USER,
            [application.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Error sending status email: {e}")

    return redirect('hr_dashboard')


@login_required
def edit_hr_profile(request):
    # NOTE: kept as-is structurally, but flagging: the POST branch never actually
    # updates anything (it's `pass`). If you want this page to work, it needs a
    # bound form (e.g. HRRegistrationForm or a dedicated HRProfileForm) saved here.
    try:
        hr_profile = request.user.hr_profile
    except HRProfile.DoesNotExist:
        hr_profile = None

    if request.method == 'POST':
        # TODO: bind a form to `request.POST`/`request.FILES` and call form.save()
        pass

    return render(request, 'core/edit_hr_profile.html', {'hr_profile': hr_profile})

# இந்த பங்க்ஷனை views.py-ன் கடைசியில் சேர்த்து விடுங்கள்
@login_required
def update_status(request, id, status):
    # அப்ளிகேஷனை எடுக்கிறோம்
    application = get_object_or_404(JobApplication, id=id)
    
    # ஸ்டேட்டஸை அப்டேட் பண்றோம் (Accepted or Rejected)
    application.status = status
    application.save()
    
    # HR டேஷ்போர்டுக்கு ரீடைரக்ட் பண்றோம்
    return redirect('hr_dashboard')

def about_view(request):
    return render(request, 'core/about.html')
