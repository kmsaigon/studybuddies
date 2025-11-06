from django import forms
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from django.db import OperationalError, connection
from .models import Profile, University, Course


class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join([f'<div class="alert alert-danger" role="alert">{e}</div>' for e in self]))


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'full_name', 'avatar', 'university', 'grade_level', 'major',
            'current_courses', 'availability_json', 'modality_pref',
            'campus_name', 'latitude', 'longitude', 'commute_radius_miles',
            'study_prefs', 'visibility'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'university': forms.Select(attrs={'class': 'form-select'}),
            'grade_level': forms.Select(attrs={'class': 'form-select'}),
            'major': forms.TextInput(attrs={'class': 'form-control'}),
            'current_courses': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'availability_json': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '{"mon":[["18:00","20:00"]], "wed":[["19:00","21:00"]]}'}),
            'modality_pref': forms.Select(attrs={'class': 'form-select'}),
            'campus_name': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'commute_radius_miles': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '99.9'}),
            'study_prefs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comma-separated tags: quiet, focused, collaborative'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def _table_exists(self, model):
        """Check if a model's database table exists"""
        try:
            table_name = model._meta.db_table
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        
        # Limit courses to active courses (handle case where table doesn't exist)
        if self._table_exists(Course):
            try:
                self.fields['current_courses'].queryset = Course.objects.filter(is_active=True)
            except Exception:
                self.fields['current_courses'] = forms.MultipleChoiceField(
                    choices=[],
                    required=False,
                    widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5', 'disabled': True})
                )
        else:
            # Table doesn't exist yet - replace with empty ChoiceField
            self.fields['current_courses'] = forms.MultipleChoiceField(
                choices=[],
                required=False,
                widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5', 'disabled': True})
            )
        
        # Set university ordering (handle case where table doesn't exist)
        if self._table_exists(University):
            try:
                self.fields['university'].queryset = University.objects.all().order_by('name')
            except Exception:
                self.fields['university'] = forms.ChoiceField(
                    choices=[('', 'Please run migrations first')],
                    required=False,
                    widget=forms.Select(attrs={'class': 'form-select', 'disabled': True})
                )
        else:
            # Table doesn't exist yet - replace with empty ChoiceField
            self.fields['university'] = forms.ChoiceField(
                choices=[('', 'Please run migrations first')],
                required=False,
                widget=forms.Select(attrs={'class': 'form-select', 'disabled': True})
            )

