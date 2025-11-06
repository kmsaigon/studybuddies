from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.conf import settings
from django.utils import timezone
from django.db.models import F
import json

from .forms import ListingForm, ListingSearchForm
from .models import BuddyListing, JoinRequest, GroupMembership, Message
from profiles.models import Profile, University
from locations.models import Location


# Utility function for distance calculation
def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in miles"""
    from math import radians, cos, sin, asin, sqrt
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    miles = 3956 * c  # Radius of earth in miles
    return miles


def parse_time(time_str):
    """Parse time string like '18:00' to time object"""
    from datetime import time
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)
    except:
        return None


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


class MyListingsView(LoginRequiredMixin, ListView):
    template_name = 'buddies/my_listings.html'
    context_object_name = 'listings'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context is None:
            context = {}
        context['template_data'] = {'title': 'My Listings'}
        return context
    
    def get_queryset(self):
        # Get all listings owned by the current user
        return BuddyListing.objects.filter(
            owner=self.request.user
        ).select_related(
            'course',
            'university',
            'location'
        ).order_by('-created_at')


class MyGroupsView(LoginRequiredMixin, ListView):
    template_name = 'buddies/my_groups.html'
    context_object_name = 'groups'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context is None:
            context = {}
        context['template_data'] = {'title': 'My Groups'}
        
        # Add pending join requests
        context['pending_requests'] = JoinRequest.objects.filter(
            student=self.request.user,
            status='requested'
        ).select_related('listing', 'listing__course', 'listing__university')
        
        # Add membership info for each group
        memberships = GroupMembership.objects.filter(
            student=self.request.user,
            left_at__isnull=True
        ).select_related('listing')
        
        context['memberships'] = {m.listing.id: m for m in memberships}
        
        return context
    
    def get_queryset(self):
        # Get all active memberships for the current user
        memberships = GroupMembership.objects.filter(
            student=self.request.user,
            left_at__isnull=True
        ).select_related(
            'listing',
            'listing__course',
            'listing__university',
            'listing__location',
            'listing__owner'
        ).order_by('-joined_at')
        
        # Return the listings from these memberships
        return [membership.listing for membership in memberships]


class ListingCreateView(LoginRequiredMixin, CreateView):
    model = BuddyListing
    form_class = ListingForm
    template_name = 'buddies/listing_form.html'
    success_url = reverse_lazy('buddies:my_listings')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context is None:
            context = {}
        context['template_data'] = {'title': 'Create Listing'}
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        # Set university from course if not set
        if not form.instance.university and form.instance.course:
            form.instance.university = form.instance.course.university
        # Save the listing
        response = super().form_valid(form)
        # Create initial membership for owner
        GroupMembership.objects.create(
            listing=self.object,
            student=self.request.user,
            role='owner'
        )
        messages.success(self.request, 'Listing created successfully!')
        return response


class ListingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BuddyListing
    form_class = ListingForm
    template_name = 'buddies/listing_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context is None:
            context = {}
        context['template_data'] = {'title': 'Edit Listing'}
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def test_func(self):
        listing = self.get_object()
        return listing.owner == self.request.user
    
    def get_success_url(self):
        return reverse('buddies:listing_detail', kwargs={'slug': self.object.slug})


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
            context['is_member'] = listing.memberships.filter(
                student=self.request.user,
                left_at__isnull=True
            ).exists()
            context['is_owner'] = listing.owner == self.request.user
            
            # Check for existing join request
            existing_request = listing.join_requests.filter(
                student=self.request.user,
                status__in=['requested', 'waitlisted']
            ).first()
            context['has_requested'] = existing_request is not None
            context['join_request'] = existing_request
            
            # Can join if: not a member, not owner, hasn't requested, and group is open
            context['can_join'] = (
                not context['is_member'] and 
                not context['is_owner'] and 
                not context['has_requested'] and
                listing.status == 'open'
            )
        
        # Get members
        context['members'] = listing.memberships.filter(
            left_at__isnull=True
        ).select_related('student', 'student__profile')
        
        # Get member count
        context['member_count'] = context['members'].count()
        context['spots_available'] = listing.capacity - context['member_count']
        
        return context


@login_required
def request_join(request, slug):
    """Handle join request submission"""
    listing = get_object_or_404(BuddyListing, slug=slug)
    
    # Check if user is already a member
    if listing.memberships.filter(student=request.user, left_at__isnull=True).exists():
        messages.warning(request, 'You are already a member of this group.')
        return redirect('buddies:listing_detail', slug=slug)
    
    # Check if user is the owner
    if listing.owner == request.user:
        messages.warning(request, 'You cannot join your own listing.')
        return redirect('buddies:listing_detail', slug=slug)
    
    # Check if listing is open
    if listing.status != 'open':
        messages.error(request, 'This listing is not accepting new members.')
        return redirect('buddies:listing_detail', slug=slug)
    
    # Check for existing request
    existing_request = JoinRequest.objects.filter(
        listing=listing,
        student=request.user,
        status__in=['requested', 'waitlisted']
    ).first()
    
    if existing_request:
        messages.warning(request, 'You have already requested to join this group.')
        return redirect('buddies:listing_detail', slug=slug)
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        
        # Check capacity
        current_members = listing.memberships.filter(left_at__isnull=True).count()
        
        if listing.join_policy == 'auto_accept':
            # Auto-accept if there's space
            if current_members < listing.capacity:
                # Create membership directly
                GroupMembership.objects.create(
                    listing=listing,
                    student=request.user,
                    role='member'
                )
                
                # Update current_size
                listing.current_size = current_members + 1
                if listing.current_size >= listing.capacity:
                    listing.status = 'filled'
                listing.save()
                
                # Create an auto-accepted join request for record-keeping
                JoinRequest.objects.create(
                    listing=listing,
                    student=request.user,
                    message=message_text,
                    status='accepted'
                )
                
                messages.success(request, f'You have successfully joined "{listing.title}"!')
                return redirect('buddies:my_groups')
            else:
                # Create waitlisted request
                JoinRequest.objects.create(
                    listing=listing,
                    student=request.user,
                    message=message_text,
                    status='waitlisted'
                )
                messages.info(request, 'This group is full. You have been added to the waitlist.')
                return redirect('buddies:listing_detail', slug=slug)
        else:
            # Owner approval required
            status = 'requested' if current_members < listing.capacity else 'waitlisted'
            JoinRequest.objects.create(
                listing=listing,
                student=request.user,
                message=message_text,
                status=status
            )
            
            if status == 'waitlisted':
                messages.info(request, 'This group is full. Your request has been added to the waitlist.')
            else:
                messages.success(request, 'Your join request has been submitted. The owner will review it shortly.')
            
            return redirect('buddies:listing_detail', slug=slug)
    
    # GET request - show join request form
    template_data = {'title': f'Join {listing.title}'}
    return render(request, 'buddies/join_request.html', {
        'template_data': template_data,
        'listing': listing
    })


@login_required
def withdraw_request(request, slug):
    """Withdraw a pending join request"""
    listing = get_object_or_404(BuddyListing, slug=slug)
    
    if request.method == 'POST':
        join_request = get_object_or_404(
            JoinRequest,
            listing=listing,
            student=request.user,
            status__in=['requested', 'waitlisted']
        )
        
        join_request.status = 'withdrawn'
        join_request.save()
        
        messages.success(request, 'Your join request has been withdrawn.')
        return redirect('buddies:listing_detail', slug=slug)
    
    return redirect('buddies:listing_detail', slug=slug)


@login_required
def leave_group(request, slug):
    """Leave a study group"""
    listing = get_object_or_404(BuddyListing, slug=slug)
    
    # Check if user is a member
    membership = get_object_or_404(
        GroupMembership,
        listing=listing,
        student=request.user,
        left_at__isnull=True
    )
    
    # Owner cannot leave their own group
    if membership.role == 'owner':
        messages.error(request, 'As the owner, you cannot leave this group. You can cancel the listing instead.')
        return redirect('buddies:listing_detail', slug=slug)
    
    if request.method == 'POST':
        # Mark membership as left
        membership.left_at = timezone.now()
        membership.save()
        
        # Update current_size
        listing.current_size = listing.memberships.filter(left_at__isnull=True).count()
        
        # If group was filled, reopen it
        if listing.status == 'filled' and listing.current_size < listing.capacity:
            listing.status = 'open'
        
        listing.save()
        
        # Check if there are waitlisted requests to promote
        if listing.status == 'open':
            waitlisted = listing.join_requests.filter(status='waitlisted').first()
            if waitlisted and listing.join_policy == 'auto_accept':
                # Auto-promote from waitlist
                GroupMembership.objects.create(
                    listing=listing,
                    student=waitlisted.student,
                    role='member'
                )
                waitlisted.status = 'accepted'
                waitlisted.save()
                
                listing.current_size += 1
                if listing.current_size >= listing.capacity:
                    listing.status = 'filled'
                listing.save()
        
        messages.success(request, f'You have left "{listing.title}".')
        return redirect('buddies:my_groups')
    
    # GET request - show confirmation page
    template_data = {'title': f'Leave {listing.title}'}
    return render(request, 'buddies/leave_confirm.html', {
        'template_data': template_data,
        'listing': listing
    })


@login_required
def request_thread(request, pk):
    template_data = {'title': 'Request Thread'}
    return render(request, 'buddies/request_thread.html', {'template_data': template_data})


@login_required
def close_listing(request, slug):
    """Close a listing (mark as filled)"""
    listing = get_object_or_404(BuddyListing, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        listing.status = 'filled'
        listing.save()
        messages.success(request, 'Listing has been closed.')
        return redirect('buddies:listing_detail', slug=slug)
    
    return redirect('buddies:listing_detail', slug=slug)


@login_required
def cancel_listing(request, slug):
    """Cancel a listing"""
    listing = get_object_or_404(BuddyListing, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        listing.status = 'cancelled'
        listing.save()
        
        # Notify all members
        messages.success(request, 'Listing has been cancelled.')
        return redirect('buddies:my_listings')
    
    return redirect('buddies:listing_detail', slug=slug)


@login_required
def roster_view(request, slug):
    """View all members of a study group"""
    listing = get_object_or_404(BuddyListing, slug=slug)
    
    # Check if user is a member or owner
    is_member = listing.memberships.filter(
        student=request.user,
        left_at__isnull=True
    ).exists()
    
    if not is_member and listing.owner != request.user:
        messages.error(request, 'You must be a member to view the roster.')
        return redirect('buddies:listing_detail', slug=slug)
    
    members = listing.memberships.filter(
        left_at__isnull=True
    ).select_related('student', 'student__profile').order_by('-role', 'joined_at')
    
    template_data = {'title': f'Roster - {listing.title}'}
    return render(request, 'buddies/roster.html', {
        'template_data': template_data,
        'listing': listing,
        'members': members
    })


@login_required
def requests_queue(request, slug):
    """View pending join requests (owner only)"""
    listing = get_object_or_404(BuddyListing, slug=slug, owner=request.user)
    
    pending_requests = listing.join_requests.filter(
        status__in=['requested', 'waitlisted']
    ).select_related('student', 'student__profile').order_by('created_at')
    
    template_data = {'title': f'Join Requests - {listing.title}'}
    return render(request, 'buddies/requests_queue.html', {
        'template_data': template_data,
        'listing': listing,
        'requests': pending_requests
    })


@login_required
def request_decision(request, slug, pk):
    """Accept or decline a join request (owner only)"""
    listing = get_object_or_404(BuddyListing, slug=slug, owner=request.user)
    join_request = get_object_or_404(JoinRequest, pk=pk, listing=listing)
    
    if request.method == 'POST':
        decision = request.POST.get('decision')
        
        if decision == 'accept':
            # Check capacity
            current_members = listing.memberships.filter(left_at__isnull=True).count()
            
            if current_members < listing.capacity:
                # Create membership
                GroupMembership.objects.create(
                    listing=listing,
                    student=join_request.student,
                    role='member'
                )
                
                # Update request status
                join_request.status = 'accepted'
                join_request.save()
                
                # Update listing
                listing.current_size = current_members + 1
                if listing.current_size >= listing.capacity:
                    listing.status = 'filled'
                listing.save()
                
                messages.success(request, f'{join_request.student.username} has been added to the group.')
            else:
                messages.error(request, 'The group is full.')
        
        elif decision == 'decline':
            join_request.status = 'declined'
            join_request.save()
            messages.success(request, 'Join request has been declined.')
        
        return redirect('buddies:requests_queue', slug=slug)
    
    return redirect('buddies:requests_queue', slug=slug)


@login_required
def remove_member(request, slug, user_id):
    """Remove a member from the group (owner only)"""
    listing = get_object_or_404(BuddyListing, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        membership = get_object_or_404(
            GroupMembership,
            listing=listing,
            student__id=user_id,
            left_at__isnull=True
        )
        
        # Cannot remove owner
        if membership.role == 'owner':
            messages.error(request, 'Cannot remove the owner.')
            return redirect('buddies:roster', slug=slug)
        
        # Mark as left
        membership.left_at = timezone.now()
        membership.save()
        
        # Update listing
        listing.current_size = listing.memberships.filter(left_at__isnull=True).count()
        if listing.status == 'filled' and listing.current_size < listing.capacity:
            listing.status = 'open'
        listing.save()
        
        messages.success(request, 'Member has been removed.')
        return redirect('buddies:roster', slug=slug)
    
    return redirect('buddies:roster', slug=slug)


@login_required
def group_chat(request, slug):
    """Group chat for members"""
    listing = get_object_or_404(BuddyListing, slug=slug)
    
    # Check if user is a member
    is_member = listing.memberships.filter(
        student=request.user,
        left_at__isnull=True
    ).exists()
    
    if not is_member and listing.owner != request.user:
        messages.error(request, 'You must be a member to access the group chat.')
        return redirect('buddies:listing_detail', slug=slug)
    
    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        if message_text:
            Message.objects.create(
                listing=listing,
                sender=request.user,
                body=message_text
            )
            messages.success(request, 'Message sent.')
            return redirect('buddies:group_chat', slug=slug)
    
    # Get all messages for this listing
    chat_messages = listing.messages.select_related('sender').order_by('created_at')
    
    template_data = {'title': f'Chat - {listing.title}'}
    return render(request, 'buddies/group_chat.html', {
        'template_data': template_data,
        'listing': listing,
        'messages': chat_messages
    })