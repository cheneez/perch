from django.contrib import admin

from .models import Group, GroupInvite, GroupMembership, GroupSavedListing


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "chat_conversation", "created_at")
    search_fields = ("name", "owner__username", "owner__email")
    list_select_related = ("owner", "chat_conversation")


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("group", "user", "joined_at")
    search_fields = ("group__name", "user__username", "user__email")
    list_select_related = ("group", "user")


@admin.register(GroupInvite)
class GroupInviteAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "inviter", "invitee", "status", "created_at", "responded_at")
    list_filter = ("status",)
    search_fields = ("group__name", "inviter__username", "invitee__username")
    list_select_related = ("group", "inviter", "invitee")


@admin.register(GroupSavedListing)
class GroupSavedListingAdmin(admin.ModelAdmin):
    list_display = ("group", "listing", "saved_by", "created_at")
    search_fields = ("group__name", "listing__title", "saved_by__username")
    list_select_related = ("group", "listing", "saved_by")
