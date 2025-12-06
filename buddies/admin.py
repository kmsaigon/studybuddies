from django.contrib import admin

# Import models - will work once models are imported
try:
    from .models import BuddyListing, JoinRequest, GroupMembership, ListingStatusHistory, Message, GroupRating
    
    @admin.register(BuddyListing)
    class BuddyListingAdmin(admin.ModelAdmin):
        list_display = ['title', 'course', 'university', 'owner', 'status', 'current_size', 'capacity', 'created_at']
        list_filter = ['status', 'university', 'modality', 'cadence', 'visibility', 'created_at']
        search_fields = ['title', 'description', 'course__code', 'course__name', 'owner__username']
        readonly_fields = ['created_at', 'updated_at', 'slug']
        filter_horizontal = []
        date_hierarchy = 'created_at'
    
    
    @admin.register(JoinRequest)
    class JoinRequestAdmin(admin.ModelAdmin):
        list_display = ['student', 'listing', 'status', 'created_at']
        list_filter = ['status', 'created_at']
        search_fields = ['student__username', 'listing__title']
        date_hierarchy = 'created_at'
    
    
    @admin.register(GroupMembership)
    class GroupMembershipAdmin(admin.ModelAdmin):
        list_display = ['student', 'listing', 'role', 'joined_at', 'left_at']
        list_filter = ['role', 'joined_at']
        search_fields = ['student__username', 'listing__title']
    
    
    @admin.register(ListingStatusHistory)
    class ListingStatusHistoryAdmin(admin.ModelAdmin):
        list_display = ['listing', 'old_status', 'new_status', 'changed_by', 'timestamp']
        list_filter = ['timestamp']
        search_fields = ['listing__title']
        readonly_fields = ['timestamp']
    
    
    @admin.register(Message)
    class MessageAdmin(admin.ModelAdmin):
        list_display = ['sender', 'listing', 'join_request', 'created_at']
        list_filter = ['created_at']
        search_fields = ['body', 'sender__username']
        readonly_fields = ['created_at']
    
    
    @admin.register(GroupRating)
    class GroupRatingAdmin(admin.ModelAdmin):
        list_display = ['student', 'listing', 'rating', 'created_at']
        list_filter = ['rating', 'created_at']
        search_fields = ['student__username', 'listing__title', 'feedback']
        readonly_fields = ['created_at', 'updated_at']
        date_hierarchy = 'created_at'
except ImportError:
    # Models don't exist yet - admin registrations will be available once models are imported
    pass
