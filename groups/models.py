from django.conf import settings
from django.db import models

from chat.models import Conversation


class Group(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_groups",
    )
    chat_conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name="group_record",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "-created_at"]

    def __str__(self):
        return f"{self.name} (owner={self.owner_id})"


class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("group", "user"),
                name="groups_membership_group_user_uniq",
            ),
        ]
        ordering = ["joined_at"]

    def __str__(self):
        return f"group={self.group_id} user={self.user_id}"


class GroupInvite(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="invites")
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_group_invites",
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_group_invites",
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"invite={self.id} group={self.group_id} {self.inviter_id}->{self.invitee_id} ({self.status})"


class GroupSavedListing(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="saved_listings")
    listing = models.ForeignKey("listings.Listing", on_delete=models.CASCADE, related_name="saved_by_groups")
    saved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_saved_listings",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("group", "listing"),
                name="groups_savedlisting_group_listing_uniq",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"group={self.group_id} listing={self.listing_id} by={self.saved_by_id}"
