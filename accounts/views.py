from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        try:
            user = User.objects.get(email=email)
            user = authenticate(username=user.username, password=password)
            if user:
                login(request, user)
                return redirect('/auth/dashboard/')
            else:
                messages.error(request, 'Wrong password')
        except User.DoesNotExist:
            messages.error(request, 'No account found')
    return render(request, 'accounts/login.html')

def signup_view(request):
    if request.method == 'POST':
        first_name       = request.POST['first_name']
        last_name        = request.POST['last_name']
        email            = request.POST['email']
        password         = request.POST['password']
        confirm_password = request.POST['confirm_password']
        user_type        = request.POST.get('user_type', 'student')

        # Check BC email
        if not email.endswith('@bc.edu'):
            messages.error(request, '❌ Must use a valid @bc.edu email address')
            return render(request, 'accounts/signup.html')

        # Check passwords match
        if password != confirm_password:
            messages.error(request, '❌ Passwords do not match')
            return render(request, 'accounts/signup.html')

        # Check password length
        if len(password) < 8:
            messages.error(request, '❌ Password must be at least 8 characters')
            return render(request, 'accounts/signup.html')

        # Check email not already used
        if User.objects.filter(email=email).exists():
            messages.error(request, '❌ An account with that email already exists')
            return render(request, 'accounts/signup.html')

        username = email.split('@')[0]
        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name
        )
        Profile.objects.create(user=user, user_type=user_type)
        login(request, user)
        return redirect('/auth/verify/')
    return render(request, 'accounts/signup.html')

def logout_view(request):
    logout(request)
    return redirect('/auth/login/')

def verify_view(request):
    return render(request, 'accounts/verify.html')

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('/auth/login/')
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'student'}
    )
    return render(request, 'accounts/dashboard.html', {
        'user': request.user,
        'user_type': profile.user_type
    })
