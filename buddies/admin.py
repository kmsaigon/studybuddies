from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import BuddyListing, JoinRequest, GroupMembership, Message
from profiles.models import Profile
# Import models - will work once models are imported

from .models import BuddyListing, JoinRequest, GroupMembership, ListingStatusHistory, Message, GroupRating
    
@admin.register(BuddyListing)
class BuddyListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'university', 'owner', 'status', 'current_size', 'capacity', 'created_at']
    list_filter = ['status', 'university', 'modality', 'cadence', 'visibility', 'created_at']
    search_fields = ['title', 'description', 'course__code', 'course__name', 'owner__username']
    readonly_fields = ['created_at', 'updated_at', 'slug']
    filter_horizontal = []
    date_hierarchy = 'created_at'
    actions = ['mark_as_closed', 'mark_as_cancelled', 'delete_listing']
"""
    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
        self.message_user(request, f"{queryset.count()} listings marked as closed.")
    mark_as_closed.short_description = "Close selected listings"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"{queryset.count()} listings cancelled.")
    mark_as_cancelled.short_description = "Cancel selected listings"
    
    def delete_listing(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} listings deleted.")
    delete_listing.short_description = "Delete selected listings"

"""

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
    actions = ['remove_from_group']

    def remove_from_group(self, request, queryset):
        from django.utils import timezone
        queryset.update(left_at=timezone.now())
        self.message_user(request, f"{queryset.count()} members removed from groups.")
    remove_from_group.short_description = "Remove selected members from groups"

    

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
    actions = ['delete_messages']
"""
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Message Preview'
    
    def delete_messages(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} messages deleted.")
    delete_messages.short_description = "Delete selected messages"
"""

@admin.register(GroupRating)
class GroupRatingAdmin(admin.ModelAdmin):
    list_display = ['student', 'listing', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['student__username', 'listing__title', 'feedback']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['university', 'major', 'graduation_year', 'bio']


class CustomUserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    actions = ['deactivate_users', 'activate_users', 'ban_users']
""""
def deactivate_users(self, request, queryset):
    queryset.update(is_active=False)
    self.message_user(request, f"{queryset.count()} users deactivated.")
deactivate_users.short_description = "Deactivate selected users"

def activate_users(self, request, queryset):
    queryset.update(is_active=True)
    self.message_user(request, f"{queryset.count()} users activated.")
activate_users.short_description = "Activate selected users"

def ban_users(self, request, queryset):
    # Deactivate and remove from all groups
    queryset.update(is_active=False)
    for user in queryset:
        GroupMembership.objects.filter(student=user, left_at__isnull=True).update(
            left_at=timezone.now()
        )
    self.message_user(request, f"{queryset.count()} users banned and removed from all groups.")
ban_users.short_description = "Ban selected users (deactivate + remove from groups)"
"""
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)