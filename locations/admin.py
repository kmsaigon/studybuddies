from django.contrib import admin, messages
from .utils import geocode_address

# Import Location model - will work once model is imported
try:
    from .models import Location
    
    @admin.register(Location)
    class LocationAdmin(admin.ModelAdmin):
        list_display = ('name', 'university', 'address', 'latitude', 'longitude', 'is_active', 'created_at')
        list_filter = ('university', 'is_active', 'created_at')
        search_fields = ('name', 'address', 'university__name')
        
        def save_model(self, request, obj, form, change):
            """
            Auto-geocode location if coordinates are missing and address is provided.
            """
            # Only geocode if lat/lng are empty and address is provided
            if (not obj.latitude or not obj.longitude) and obj.address:
                try:
                    coordinates = geocode_address(obj.address)
                    if coordinates:
                        obj.latitude, obj.longitude = coordinates
                        messages.success(request, f'Successfully geocoded address: {obj.address}')
                    else:
                        messages.warning(request, f'Could not geocode address: {obj.address}. Please enter coordinates manually.')
                except Exception as e:
                    messages.error(request, f'Error geocoding address: {str(e)}')
            
            super().save_model(request, obj, form, change)
except ImportError:
    # Location model doesn't exist yet - admin registration will be available once model is imported
    pass
