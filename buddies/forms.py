from django import forms
from .models import BuddyListing, JoinRequest, Message
from profiles.models import University, Course
from locations.models import Location


class ListingForm(forms.ModelForm):
    class Meta:
        model = BuddyListing
        fields = [
            'university', 'course', 'title', 'description', 'modality',
            'location', 'meeting_link', 'capacity', 'cadence', 'weekday',
            'start_time', 'end_time', 'tags', 'join_policy', 'visibility'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'university': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'modality': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 50}),
            'cadence': forms.Select(attrs={'class': 'form-select'}),
            'weekday': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'midterm 1, op-amps'}),
            'join_policy': forms.Select(attrs={'class': 'form-select'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit locations to active locations
        self.fields['location'].queryset = Location.objects.filter(is_active=True)
        
        # If user has profile, pre-fill university
        if user and hasattr(user, 'profile') and user.profile.university:
            self.fields['university'].initial = user.profile.university
            # Limit courses to user's university
            self.fields['course'].queryset = Course.objects.filter(
                university=user.profile.university,
                is_active=True
            )
        else:
            self.fields['course'].queryset = Course.objects.filter(is_active=True)
    
    def clean(self):
        cleaned = super().clean()
        cadence = cleaned.get('cadence')
        weekday = cleaned.get('weekday')
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')
        
        # Weekly cadence requires weekday
        if cadence == 'weekly' and not weekday:
            self.add_error('weekday', 'Weekday is required for weekly cadence.')
        
        # Time validation
        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', 'End time must be after start time.')
        
        return cleaned
    
class ListingSearchForm(forms.Form):
    course = forms.ModelChoiceField(
    queryset=Course.objects.filter(is_active=True),
    required=False,
    widget=forms.Select(attrs={'class': 'form-select'})
    )

    university = forms.ModelChoiceField(
        queryset=University.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    modality = forms.ChoiceField(
        choices=[('', 'Any')] + list(BuddyListing.MODALITY_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    weekday = forms.ChoiceField(
        choices=[('', 'Any')] + list(BuddyListing.WEEKDAY_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    time_range = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 18:00-20:00'
        }),
        help_text='Time range (HH:MM-HH:MM)'
    )

    distance = forms.ChoiceField(
        choices=[
            ('', 'Any distance'),
            ('5', 'Within 5 miles'),
            ('10', 'Within 10 miles'),
            ('25', 'Within 25 miles'),
            ('50', 'Within 50 miles'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    capacity_remaining = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Only show listings with available spots'
    )

    status = forms.ChoiceField(
        choices=[('', 'All')] + list(BuddyListing.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='open'
    )

    # Hidden fields for distance filtering
    user_lat = forms.FloatField(
        required=False,
        widget=forms.HiddenInput()
    )
    user_lng = forms.FloatField(
        required=False,
        widget=forms.HiddenInput()
    )

    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('distance', 'Distance'),
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
