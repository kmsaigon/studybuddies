from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Note: Profile is not auto-created because it requires university and other fields.
    Users will be redirected to create their profile after signup via the profile creation view.
    """
    # Profile creation is handled manually through the profile creation view
    # after user signup, as it requires university, full_name, and grade_level
    pass

