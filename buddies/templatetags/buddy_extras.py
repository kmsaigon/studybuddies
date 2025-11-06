from django import template

register = template.Library()


@register.filter
def can_join(listing, user):
    """Check if user can join the listing"""
    if not user.is_authenticated:
        return False
    # Check if already a member
    if listing.memberships.filter(student=user, left_at__isnull=True).exists():
        return False
    # Check if already requested
    if listing.join_requests.filter(student=user, status="requested").exists():
        return False
    # Check if listing is open and has capacity
    if listing.status != "open" or listing.current_size >= listing.capacity:
        return False
    return True


@register.filter
def is_member(listing, user):
    """Check if user is a member of the listing"""
    if not user.is_authenticated:
        return False
    return listing.memberships.filter(student=user, left_at__isnull=True).exists()


@register.filter
def is_owner(listing, user):
    """Check if user is the owner of the listing"""
    if not user.is_authenticated:
        return False
    return listing.owner == user

