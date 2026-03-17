from django.contrib import admin
from django.urls import path, include

from .views import landing_page

urlpatterns = [
    path("", landing_page, name="landing"),
    path("admin/", admin.site.urls),
    path("auth/", include("accounts.urls")),
    path("student/", include("student.urls")),
    path("lessor/", include("lessor.urls")),
    path("listings/", include("listings.urls")),
]
