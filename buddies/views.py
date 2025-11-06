from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import JsonResponse
from .forms import ListingForm, ListingSearchForm
from .models import BuddyListing
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


def listing_map(request):
    template_data = {'title': 'Study Groups Map'}
    return render(request, 'buddies/map.html', {'template_data': template_data})


def api_filter_by_distance(request):
    return JsonResponse({'listings': []})


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
    template_name = 'buddies/listing_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context is None:
            context = {}
        context['template_data'] = {'title': 'Create Listing'}
        return context
    
    def get_object(self):
        return None


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
    template_name = 'buddies/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['template_data'] = {'title': 'Study Group Details'}
        return context
    
    def get_object(self):
        return None


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