from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from .views import landing_page
from .search_views import user_search

urlpatterns = [
    path("", landing_page, name="landing"),
    path("search/users/", user_search, name="user_search"),
    path("admin/", admin.site.urls),
    path("auth/", include("accounts.urls")),
    path("student/", include("student.urls")),
    path("lessor/", include("lessor.urls")),
    path("listings/", include("listings.urls")),
    path("reports/", include("moderation.urls")),
    path("notifications/", include("notifications.urls")),
    path("chat/", include("chat.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
