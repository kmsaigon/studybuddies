from django.db import models
from profiles.models import University


class Location(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=150, help_text="e.g., CULC 3rd floor")
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("university", "name")
        ordering = ['name']
    
    def __str__(self):
        if self.address:
            return f"{self.university.name} - {self.name} ({self.address})"
        return f"{self.university.name} - {self.name}"

