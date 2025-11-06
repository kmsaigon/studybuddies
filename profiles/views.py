from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Profile, Course, University
from .forms import ProfileEditForm
from buddies.models import GroupMembership, JoinRequest


@login_required
def create(request):
    """Create a new profile for the user"""
    # Check if user already has a profile
    try:
        profile = request.user.profile
        # If we get here, profile exists
        messages.info(request, 'You already have a profile. Redirecting to edit.')
        return redirect('profiles:profiles.edit')
    except Exception:
        # Profile doesn't exist or table doesn't exist yet - continue to create
        pass
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            form.save_m2m()  # Save many-to-many fields
            messages.success(request, 'Profile created successfully!')
            return redirect('profiles:profiles.detail')
    else:
        form = ProfileEditForm()
    
    context = {
        'template_data': {
            'form': form,
            'title': 'Create Profile'
        }
    }
    return render(request, 'profiles/create.html', context)


@login_required
def detail(request):
    """View the user's profile"""
    profile = get_object_or_404(Profile, user=request.user)
    
    # Get active memberships
    memberships = GroupMembership.objects.filter(
        student=request.user,
        left_at__isnull=True
    ).select_related(
        'listing',
        'listing__course',
        'listing__university'
    ).order_by('-joined_at')
    
    my_groups = [m.listing for m in memberships]
    
    # Get pending join requests
    pending_requests = JoinRequest.objects.filter(
        student=request.user,
        status__in=['requested', 'waitlisted']
    ).select_related(
        'listing',
        'listing__course'
    ).order_by('-created_at')
    
    context = {
        'template_data': {
            'profile': profile,
            'title': 'My Profile'
        },
        'profile': profile,
        'my_groups': my_groups,
        'memberships': memberships,
        'pending_requests': pending_requests,
    }
    return render(request, 'profiles/detail.html', context)


@login_required
def edit(request):
    """Edit the user's profile"""
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            form.save_m2m()  # Save many-to-many fields
            messages.success(request, 'Profile updated successfully!')
            return redirect('profiles:profiles.detail')
    else:
        form = ProfileEditForm(instance=profile)
    
    context = {
        'template_data': {
            'form': form,
            'profile': profile,
            'title': 'Edit Profile'
        }
    }
    return render(request, 'profiles/edit.html', context)


@login_required
def course_lookup_api(request):
    """AJAX endpoint for course search"""
    query = request.GET.get('q', '').strip()
    university_id = request.GET.get('university_id', '')
    
    if not query or len(query) < 2:
        return JsonResponse({'courses': []})
    
    courses = Course.objects.filter(is_active=True)
    
    if university_id:
        try:
            university = University.objects.get(pk=university_id)
            courses = courses.filter(university=university)
        except University.DoesNotExist:
            pass
    
    # Search by code or name
    courses = courses.filter(
        Q(code__icontains=query) | Q(name__icontains=query)
    )[:10]
    
    results = [
        {
            'id': course.id,
            'code': course.code,
            'name': course.name,
            'university': course.university.name,
            'display': f"{course.code} - {course.name}"
        }
        for course in courses
    ]
    
    return JsonResponse({'courses': results})