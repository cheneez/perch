from django.contrib import admin

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'school', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'user__email')
