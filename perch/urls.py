from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('accounts.urls')),
    path('student/', include('student.urls')),
    path('lessor/', include('lessor.urls')),
    path('listings/', include('listings.urls')),
]
