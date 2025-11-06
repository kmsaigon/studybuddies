from django import template
from django.db import OperationalError
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name: str) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    return user.groups.filter(name=group_name).exists() or getattr(user, 'is_superuser', False)


@register.filter(name='has_profile')
def has_profile(user):
    """Safely check if user has a profile, handling database errors gracefully"""
    if not getattr(user, 'is_authenticated', False):
        return False
    try:
        # Try to access the profile - this will query the database
        # If the table doesn't exist or profile doesn't exist, catch the exception
        profile = user.profile
        return True
    except Exception:
        # Profile doesn't exist, table doesn't exist yet, or any other error
        # Catch all exceptions to be safe
        return False

