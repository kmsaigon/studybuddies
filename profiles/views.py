from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


@login_required
def create(request):
    template_data = {}
    template_data['title'] = 'Create Profile'
    return render(request, 'profiles/create.html', {'template_data': template_data})


@login_required
def detail(request):
    template_data = {}
    template_data['title'] = 'Profile'
    return render(request, 'profiles/detail.html', {'template_data': template_data})


@login_required
def edit(request):
    template_data = {}
    template_data['title'] = 'Edit Profile'
    return render(request, 'profiles/edit.html', {'template_data': template_data})


@login_required
def course_lookup_api(request):
    # Placeholder for AJAX endpoint
    return JsonResponse({'courses': []})

