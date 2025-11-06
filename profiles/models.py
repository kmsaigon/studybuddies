from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Index


class University(models.Model):
    name = models.CharField(max_length=150, unique=True, db_index=True)
    domain = models.CharField(max_length=120, blank=True, help_text="e.g., gatech.edu")
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Universities"
        ordering = ['name']


class Course(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="courses")
    code = models.CharField(max_length=20, help_text="e.g., CS 2340")
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.code} {self.name}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        unique_together = ("university", "code")
        indexes = [
            Index(fields=["university", "code"]),
        ]
        ordering = ['code']


class Profile(models.Model):
    GRADE_LEVEL_CHOICES = [
        ("frosh", "First-year"),
        ("soph", "Sophomore"),
        ("jun", "Junior"),
        ("sen", "Senior"),
        ("grad", "Graduate"),
        ("other", "Other"),
    ]
    
    MODALITY_PREF_CHOICES = [
        ("in_person", "In-person"),
        ("online", "Online"),
        ("either", "Either"),
    ]
    
    VISIBILITY_CHOICES = [
        ("same_school", "Same-school only"),
        ("public", "Platform-wide"),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=120)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="profiles")
    grade_level = models.CharField(max_length=10, choices=GRADE_LEVEL_CHOICES)
    major = models.CharField(max_length=120, blank=True)
    current_courses = models.ManyToManyField(Course, related_name="enrolled_profiles", blank=True)
    availability_json = models.JSONField(default=dict, blank=True, help_text="e.g., {'mon':[['18:00','20:00']], 'wed':[['19:00','21:00']]}")
    modality_pref = models.CharField(max_length=10, choices=MODALITY_PREF_CHOICES, default="either")
    campus_name = models.CharField(max_length=150, blank=True, help_text="e.g., Clough Commons")
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    commute_radius_miles = models.DecimalField(max_digits=4, decimal_places=1, default=5.0, help_text="0.0-99.9")
    study_prefs = models.TextField(blank=True, help_text="Comma-separated tags")
    visibility = models.CharField(max_length=15, choices=VISIBILITY_CHOICES, default="same_school")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} ({self.user.username})"
    
    class Meta:
        ordering = ['-created_at']
