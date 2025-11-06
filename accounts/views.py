from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.contrib import messages

from .forms import CustomUserCreationForm, CustomErrorList


@login_required
def logout(request):
    auth_logout(request)
    return redirect('home:index')


def login(request):
    template_data = {'title': 'Login'}
    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'template_data': template_data})
    user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
    if user is None:
        template_data['error'] = 'The username or password is incorrect.'
        return render(request, 'accounts/login.html', {'template_data': template_data})
    auth_login(request, user)
    
    # Check if user has a profile, redirect to profile creation if not
    try:
        # Try to access the profile - if it doesn't exist, this will raise an exception
        user.profile
    except Exception:
        # Profile doesn't exist - redirect to profile creation
        messages.info(request, 'Please create your profile to continue.')
        return redirect('profiles:profiles.create')
    
    return redirect('home:dashboard')


def signup(request):
    template_data = {'title': 'Sign Up'}
    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html', {'template_data': template_data})
    form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)
    if form.is_valid():
        user = form.save()
        # Don't auto-login, redirect to login page instead
        messages.success(request, 'Account created successfully! Please log in to continue.')
        return redirect('accounts:login')
    template_data['form'] = form
    return render(request, 'accounts/signup.html', {'template_data': template_data})
