from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User


def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    return render(request, 'accounts/signup.html', {'template_data': template_data})


def login_view(request):
    template_data = {}
    template_data['title'] = 'Login'
    return render(request, 'accounts/login.html', {'template_data': template_data})


@login_required
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home:index')

