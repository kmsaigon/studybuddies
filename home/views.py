from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def index(request):
    template_data = {}
    template_data['title'] = 'StudyBuddies'
    return render(request, 'home/index.html', {'template_data': template_data})


def about(request):
    template_data = {}
    template_data['title'] = 'About'
    return render(request, 'home/about.html', {'template_data': template_data})


@login_required
def dashboard(request):
    template_data = {}
    template_data['title'] = 'Dashboard'
    return render(request, 'home/dashboard.html', {'template_data': template_data})

