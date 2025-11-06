from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import JsonResponse


class ListingSearchView(ListView):
    template_name = 'buddies/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context is None:
            context = {}
        context['template_data'] = {'title': 'Find a Study Group'}
        return context
    
    def get_queryset(self):
        return []


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

