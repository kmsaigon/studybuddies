from django.urls import path
from . import views

app_name = 'buddies'

urlpatterns = [
    # Public/search
    path('', views.ListingSearchView.as_view(), name='listing_search'),
    path('map/', views.listing_map, name='listing_map'),
    path('api/nearby/', views.api_filter_by_distance, name='api_filter_by_distance'),
    
    # Specific routes (must come before slug patterns)
    path('my/', views.MyListingsView.as_view(), name='my_listings'),
    path('my/groups/', views.MyGroupsView.as_view(), name='my_groups'),
    path('create/', views.ListingCreateView.as_view(), name='listing_create'),
    path('requests/<int:pk>/chat/', views.request_thread, name='request_thread'),
    
    # Slug-based routes (detail and actions)
    path('<slug:slug>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('<slug:slug>/edit/', views.ListingUpdateView.as_view(), name='listing_edit'),
    path('<slug:slug>/close/', views.close_listing, name='close_listing'),
    path('<slug:slug>/cancel/', views.cancel_listing, name='cancel_listing'),
    path('<slug:slug>/roster/', views.roster_view, name='roster'),
    path('<slug:slug>/requests/', views.requests_queue, name='requests_queue'),
    path('<slug:slug>/requests/<int:pk>/decision/', views.request_decision, name='request_decision'),
    path('<slug:slug>/members/<int:user_id>/remove/', views.remove_member, name='remove_member'),
    path('<slug:slug>/join/', views.request_join, name='request_join'),
    path('<slug:slug>/withdraw/', views.withdraw_request, name='withdraw_request'),
    path('<slug:slug>/leave/', views.leave_group, name='leave_group'),
    path('<slug:slug>/chat/', views.group_chat, name='group_chat'),
]

