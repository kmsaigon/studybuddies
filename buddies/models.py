from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.db.models import Index
from profiles.models import University, Course
from locations.models import Location


class BuddyListing(models.Model):
    MODALITY_CHOICES = [
        ("in_person", "In-person"),
        ("online", "Online"),
        ("hybrid", "Hybrid"),
    ]
    
    CADENCE_CHOICES = [
        ("one_off", "One-off"),
        ("weekly", "Weekly"),
    ]
    
    WEEKDAY_CHOICES = [
        ("mon", "Mon"),
        ("tue", "Tue"),
        ("wed", "Wed"),
        ("thu", "Thu"),
        ("fri", "Fri"),
        ("sat", "Sat"),
        ("sun", "Sun"),
    ]
    
    JOIN_POLICY_CHOICES = [
        ("owner_approve", "Owner approves"),
        ("auto_accept", "Auto-accept"),
    ]
    
    VISIBILITY_CHOICES = [
        ("same_school", "Same-school"),
        ("public", "Public"),
    ]
    
    STATUS_CHOICES = [
        ("open", "Open"),
        ("filled", "Filled"),
        ("cancelled", "Cancelled"),
    ]
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings")
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="listings")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="listings")
    course_code_text = models.CharField(max_length=20, blank=True, help_text="Fallback if course missing")
    title = models.CharField(max_length=120)
    description = models.TextField()
    modality = models.CharField(max_length=10, choices=MODALITY_CHOICES, default="in_person")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name="listings")
    meeting_link = models.URLField(blank=True, help_text="For online/hybrid; members only")
    capacity = models.PositiveSmallIntegerField(default=5)
    current_size = models.PositiveSmallIntegerField(default=1, help_text="Owner included; keep in sync")
    cadence = models.CharField(max_length=10, choices=CADENCE_CHOICES, default="weekly")
    weekday = models.CharField(max_length=3, choices=WEEKDAY_CHOICES, blank=True, help_text="Weekly only")
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags: midterm 1, op-amps")
    join_policy = models.CharField(max_length=15, choices=JOIN_POLICY_CHOICES, default="owner_approve")
    visibility = models.CharField(max_length=15, choices=VISIBILITY_CHOICES, default="same_school")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open", db_index=True)
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:60] or 'listing'
            self.slug = f"{base}-{self.pk or ''}".strip('-')
        super().save(*args, **kwargs)
        # Ensure slug includes ID for uniqueness
        if self.pk:
            slug_with_id = f"{slugify(self.title)[:60] or 'listing'}-{self.pk}"
            if self.slug != slug_with_id:
                self.slug = slug_with_id
                super().save(update_fields=['slug'])
    
    def __str__(self):
        return f"{self.title} - {self.course.code}"
    
    class Meta:
        indexes = [
            Index(fields=["university", "status", "created_at"]),
            Index(fields=["course", "status"]),
        ]
        ordering = ['-created_at']


class ListingStatusHistory(models.Model):
    listing = models.ForeignKey(BuddyListing, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=10)
    new_status = models.CharField(max_length=10)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Listing Status Histories"


class JoinRequest(models.Model):
    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("withdrawn", "Withdrawn"),
        ("waitlisted", "Waitlisted"),
    ]
    
    listing = models.ForeignKey(BuddyListing, on_delete=models.CASCADE, related_name="join_requests")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="join_requests")
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="requested", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("listing", "student")
        indexes = [
            Index(fields=["student", "status"]),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} -> {self.listing.title}"


class GroupMembership(models.Model):
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("member", "Member"),
    ]
    
    listing = models.ForeignKey(BuddyListing, on_delete=models.CASCADE, related_name="memberships")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ("listing", "student")
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.student.username} in {self.listing.title} ({self.role})"


class Message(models.Model):
    """Group chat + request thread messages"""
    listing = models.ForeignKey(BuddyListing, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)
    join_request = models.ForeignKey(JoinRequest, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not (self.listing or self.join_request):
            raise ValidationError("Exactly one of listing or join_request must be set.")
        if self.listing and self.join_request:
            raise ValidationError("Cannot set both listing and join_request.")
    
    def __str__(self):
        if self.listing:
            return f"Message in {self.listing.title} from {self.sender.username}"
        return f"Message in request {self.join_request.id} from {self.sender.username}"

