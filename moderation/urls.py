from django.urls import path

from . import views

app_name = 'moderation'

urlpatterns = [
    path(
        'new/<str:app_label>/<str:model>/<int:object_id>/',
        views.create_report,
        name='report_object',
    ),
]
