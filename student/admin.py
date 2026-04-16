from django.contrib import admin

from .models import StudentCompatibilitySurvey, StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'user', 'school', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'user__email')


@admin.register(StudentCompatibilitySurvey)
class StudentCompatibilitySurveyAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'graduation_year',
        'major',
        'is_completed_display',
        'updated_at',
    )
    list_filter = ('graduation_year', 'major', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(boolean=True, description='Completed')
    def is_completed_display(self, obj):
        return obj.is_completed()
