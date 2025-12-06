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
    path('my/bookmarks/', views.MyBookmarksView.as_view(), name='my_bookmarks'),
    path('create/', views.ListingCreateView.as_view(), name='listing_create'),
    path('requests/<int:pk>/chat/', views.request_thread, name='request_thread'),
    
    # Messaging routes
    path('messages/', views.MyInboxView.as_view(), name='my_inbox'),
    path('messages/<int:conversation_id>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('messages/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('messages/<int:conversation_id>/read/', views.mark_messages_read, name='mark_messages_read'),
    
    # Slug-based routes (detail and actions)
    path('<slug:slug>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('<slug:slug>/bookmark/toggle/', views.toggle_bookmark, name='toggle_bookmark'),
    path('<slug:slug>/message/', views.create_or_get_conversation, name='create_conversation'),
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
    path('<slug:slug>/rate/', views.rate_group, name='rate_group'),
    path('<slug:slug>/ratings/<int:rating_id>/delete/', views.delete_rating, name='delete_rating'),
]

