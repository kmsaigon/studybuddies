from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.db.models import Q, Count, F
from django.core.paginator import Paginator
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_time
from math import radians, sin, cos, sqrt, atan2
import json

from .forms import ListingForm, ListingSearchForm
from .models import BuddyListing, JoinRequest, GroupMembership, Message
from profiles.models import Profile, University
from locations.models import Location



class ListingSearchView(ListView):
    model = BuddyListing
    template_name = 'buddies/list.html'
    context_object_name = 'listings'
    paginate_by = 20
    
    def get_queryset(self):
        # Start with open listings by default
        queryset = BuddyListing.objects.filter(status='open').select_related(
            'course', 'university', 'location', 'owner'
        )
        
        # Apply filters from form
        form = ListingSearchForm(self.request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # Course filter
            if cleaned_data.get('course'):
                queryset = queryset.filter(course=cleaned_data['course'])
            
            # University filter
            if cleaned_data.get('university'):
                queryset = queryset.filter(university=cleaned_data['university'])
            
            # Modality filter
            if cleaned_data.get('modality'):
                queryset = queryset.filter(modality=cleaned_data['modality'])
            
            # Weekday filter
            if cleaned_data.get('weekday'):
                queryset = queryset.filter(weekday=cleaned_data['weekday'])
            
            # Time range filter (availability)
            time_range = cleaned_data.get('time_range')
            if time_range:
                try:
                    # Parse time range like "18:00-20:00"
                    if '-' in time_range:
                        start_str, end_str = time_range.split('-')
                        start_time_filter = parse_time(start_str.strip())
                        end_time_filter = parse_time(end_str.strip())
                        if start_time_filter and end_time_filter:
                            # Filter listings that overlap with this time range
                            queryset = queryset.filter(
                                start_time__lte=end_time_filter,
                                end_time__gte=start_time_filter
                            )
                except (ValueError, AttributeError):
                    pass  # Invalid time format, skip filter
            
            # Capacity filter
            if cleaned_data.get('capacity_remaining'):
                queryset = queryset.filter(current_size__lt=F('capacity'))
            
            # Status filter
            if cleaned_data.get('status'):
                queryset = queryset.filter(status=cleaned_data['status'])
            
            # Distance filter
            user_lat = cleaned_data.get('user_lat')
            user_lng = cleaned_data.get('user_lng')
            distance = cleaned_data.get('distance')
            
            if user_lat and user_lng and distance:
                try:
                    radius = float(distance)
                    filtered_listings = []
                    for listing in queryset:
                        # Include online listings regardless of distance
                        if listing.modality in ['online', 'hybrid']:
                            filtered_listings.append(listing.id)
                        # Check distance for in-person listings
                        elif listing.location and listing.location.latitude and listing.location.longitude:
                            distance_miles = haversine(
                                user_lat, user_lng,
                                float(listing.location.latitude),
                                float(listing.location.longitude)
                            )
                            if distance_miles <= radius:
                                filtered_listings.append(listing.id)
                        # Also check if user has profile with location
                        elif self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
                            profile = self.request.user.profile
                            if profile.latitude and profile.longitude:
                                distance_miles = haversine(
                                    profile.latitude, profile.longitude,
                                    float(listing.location.latitude),
                                    float(listing.location.longitude)
                                )
                                if distance_miles <= radius:
                                    filtered_listings.append(listing.id)
                    
                    queryset = queryset.filter(id__in=filtered_listings)
                except (ValueError, TypeError):
                    pass
        
        # University visibility filter
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            # Filter out same-school only listings from other universities
            other_university_listings = queryset.filter(
                visibility='same_school'
            ).exclude(university=profile.university)
            queryset = queryset.exclude(id__in=other_university_listings)
        
        # Sort
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by == 'distance' and user_lat and user_lng:
            # Would need to annotate with distance, simplified for now
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['form'] = ListingSearchForm(self.request.GET)
            context['GOOGLE_MAPS_API_KEY'] = settings.GOOGLE_MAPS_API_KEY
            
            # Add user's current groups if authenticated
            if self.request.user.is_authenticated:
                context['my_groups'] = GroupMembership.objects.filter(
                    student=self.request.user,
                    left_at__isnull=True
                ).select_related('listing')
            
            return context

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the distance (miles) between two lat/lon points."""
    R = 3958.8  # Radius of Earth in miles
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

class MyListingsView(ListView):
    template_name = 'buddies/my_listings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context is None:
            context = {}
        context['template_data'] = {'title': 'My Listings'}
        return context
    
    def get_queryset(self):
        return []


class MyGroupsView(ListView):
    template_name = 'buddies/my_groups.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context is None:
            context = {}
        context['template_data'] = {'title': 'My Groups'}
        return context
    
    def get_queryset(self):
        return []


class ListingCreateView(CreateView):
    model = BuddyListing
    form_class = ListingForm
    template_name = 'buddies/listing_form.html'
    success_url = reverse_lazy('buddies:my_listings')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        # Set university from course if not set
        if not form.instance.university and form.instance.course:
            form.instance.university = form.instance.course.university
        # Create initial membership for owner
        listing = form.save()
        GroupMembership.objects.create(
            listing=listing,
            student=self.request.user,
            role='owner'
        )
        messages.success(self.request, 'Listing created successfully!')
        return super().form_valid(form)


class ListingUpdateView(UpdateView):
    template_name = 'buddies/listing_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context is None:
            context = {}
        context['template_data'] = {'title': 'Edit Listing'}
        return context
    
    def get_object(self):
        return None


class ListingDetailView(DetailView):
   class ListingDetailView(DetailView):
    model = BuddyListing
    template_name = 'buddies/detail.html'
    context_object_name = 'listing'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return BuddyListing.objects.select_related('course', 'university', 'location', 'owner')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        listing = self.object
        
        # Check if user can join
        if self.request.user.is_authenticated:
            context['can_join'] = self._can_join(listing)
            context['is_member'] = listing.memberships.filter(
                student=self.request.user,
                left_at__isnull=True
            ).exists()
            context['is_owner'] = listing.owner == self.request.user
            context['has_requested'] = listing.join_requests.filter(
                student=self.request.user,
                status='requested'
            ).exists()
        
        # Get members
        context['members'] = listing.memberships.filter(left_at__isnull=True).select_related('student')
        
        return context
    
    def _can_join(self, listing):
        """Check if user can join the listing"""
        if not self.request.user.is_authenticated:
            return False
        if listing.status != 'open' or listing.current_size >= listing.capacity:
            return False
        if listing.memberships.filter(student=self.request.user, left_at__isnull=True).exists():
            return False
        if listing.join_requests.filter(student=self.request.user, status='requested').exists():
            return False
        return True

    
class ListingCreateView(LoginRequiredMixin, CreateView):
    model = BuddyListing
    form_class = ListingForm
    template_name = 'buddies/listing_form.html'
    success_url = reverse_lazy('buddies:my_listings')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        # Set university from course if not set
        if not form.instance.university and form.instance.course:
            form.instance.university = form.instance.course.university
        # Create initial membership for owner
        listing = form.save()
        GroupMembership.objects.create(
            listing=listing,
            student=self.request.user,
            role='owner'
        )
        messages.success(self.request, 'Listing created successfully!')
        return super().form_valid(form)
@login_required
def listing_map(request):
    """Map view of study group listings"""
    context = {
        'template_data': {
            'title': 'Study Groups Map',
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        }
    }
    return render(request, 'buddies/map.html', context)


@csrf_exempt
def api_filter_by_distance(request):
    """Return listings within a given distance"""
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
        max_distance = float(request.GET.get('distance', 10))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
    
    listings = BuddyListing.objects.filter(
        status='open',
        location__isnull=False,
        location__latitude__isnull=False,
        location__longitude__isnull=False
    ).select_related('location', 'course', 'university')
    
    filtered_listings = []
    for listing in listings:
        dist = haversine(lat, lng, float(listing.location.latitude), float(listing.location.longitude))
        if dist <= max_distance:
            filtered_listings.append({
                'id': listing.id,
                'slug': listing.slug,
                'title': listing.title,
                'course': listing.course.code,
                'latitude': float(listing.location.latitude),
                'longitude': float(listing.location.longitude),
                'distance': round(dist, 2),
                'current_size': listing.current_size,
                'capacity': listing.capacity,
            })
    
    return JsonResponse({'listings': filtered_listings})

@login_required
def request_thread(request, pk):
    template_data = {'title': 'Request Thread'}
    return render(request, 'buddies/request_thread.html', {'template_data': template_data})


@login_required
def close_listing(request, slug):
    template_data = {'title': 'Close Listing'}
    return render(request, 'buddies/list.html', {'template_data': template_data})


@login_required
def cancel_listing(request, slug):
    template_data = {'title': 'Cancel Listing'}
    return render(request, 'buddies/list.html', {'template_data': template_data})


@login_required
def roster_view(request, slug):
    template_data = {'title': 'Roster'}
    return render(request, 'buddies/roster.html', {'template_data': template_data})


@login_required
def requests_queue(request, slug):
    template_data = {'title': 'Join Requests'}
    return render(request, 'buddies/requests_queue.html', {'template_data': template_data})


@login_required
def request_decision(request, slug, pk):
    template_data = {'title': 'Request Decision'}
    return render(request, 'buddies/requests_queue.html', {'template_data': template_data})


@login_required
def remove_member(request, slug, user_id):
    template_data = {'title': 'Remove Member'}
    return render(request, 'buddies/roster.html', {'template_data': template_data})


@login_required
def request_join(request, slug):
    template_data = {'title': 'Join Request'}
    return render(request, 'buddies/join_request.html', {'template_data': template_data})


@login_required
def withdraw_request(request, slug):
    template_data = {'title': 'Withdraw Request'}
    return render(request, 'buddies/list.html', {'template_data': template_data})


@login_required
def leave_group(request, slug):
    template_data = {'title': 'Leave Group'}
    return render(request, 'buddies/my_groups.html', {'template_data': template_data})


@login_required
def group_chat(request, slug):
    template_data = {'title': 'Group Chat'}
    return render(request, 'buddies/group_chat.html', {'template_data': template_data})


