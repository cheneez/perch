from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.models import User

from .models import Favorite


try:
    admin.site.unregister(User)
except NotRegistered:
    pass


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'favorited_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = (
        'user__username',
        'favorited_user__username',
    )
