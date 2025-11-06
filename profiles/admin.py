from django.contrib import admin
from .models import University, Course, Profile


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain', 'slug', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'domain']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'university', 'is_active', 'created_at']
    list_filter = ['university', 'is_active', 'created_at']
    search_fields = ['code', 'name', 'university__name']
    prepopulated_fields = {'slug': ('code', 'name')}


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'university', 'grade_level', 'created_at']
    list_filter = ['university', 'grade_level', 'modality_pref', 'visibility', 'created_at']
    search_fields = ['full_name', 'user__username', 'major', 'university__name']
    filter_horizontal = ['current_courses']
    readonly_fields = ['created_at', 'updated_at']

