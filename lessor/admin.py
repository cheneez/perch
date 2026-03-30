from django.contrib import admin

from .models import LessorProfile


@admin.register(LessorProfile)
class LessorProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'verified', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'user__email')
