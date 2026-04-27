import urllib.parse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import Profile
from chat.models import Conversation, Message
from listings.models import Listing
from notifications.models import Notification
from student.models import StudentProfile

from .models import Group, GroupInvite, GroupMembership, GroupSavedListing


def _group_name_for_chat(group):
    return f"Group: {group.name}"


def _find_or_create_dm(user_a, user_b):
    existing = (
        Conversation.objects.filter(is_group=False, participants=user_a)
        .filter(participants=user_b)
        .first()
    )
    if existing:
        return existing

    dm = Conversation.objects.create(is_group=False, created_by=user_a)
    dm.participants.add(user_a, user_b)
    return dm


def _require_student_profile(user):
    return StudentProfile.objects.filter(user=user).exists()


class BaseStudentGroupView(RoleRequiredMixin):
    required_role = "student"

    def dispatch(self, request, *args, **kwargs):
        if not _require_student_profile(request.user):
            return redirect("student:create_profile")
        return super().dispatch(request, *args, **kwargs)


class GroupListView(BaseStudentGroupView, TemplateView):
    template_name = "groups/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groups = (
            Group.objects.filter(memberships__user=self.request.user)
            .select_related("owner")
            .prefetch_related("memberships__user")
            .distinct()
        )
        context["groups"] = groups
        context["active_group"] = None
        return context

    def post(self, request, *args, **kwargs):
        name = (request.POST.get("group_name") or "").strip()
        if len(name) < 2:
            messages.error(request, "Group name must be at least 2 characters.")
            return redirect("groups:index")

        conv = Conversation.objects.create(
            name=f"Group: {name}"[:100],
            is_group=True,
            created_by=request.user,
        )
        conv.participants.add(request.user)
        group = Group.objects.create(
            name=name[:100],
            owner=request.user,
            chat_conversation=conv,
        )
        GroupMembership.objects.create(group=group, user=request.user)
        messages.success(request, f'Group "{group.name}" created.')
        return redirect("groups:detail", group_id=group.id)


class GroupDetailView(BaseStudentGroupView, TemplateView):
    template_name = "groups/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        groups = (
            Group.objects.filter(memberships__user=self.request.user)
            .select_related("owner", "chat_conversation")
            .prefetch_related("memberships__user")
            .distinct()
        )
        active_group = get_object_or_404(
            groups,
            id=self.kwargs["group_id"],
        )
        pending_invites = active_group.invites.filter(status=GroupInvite.Status.PENDING).count()
        context["groups"] = groups
        context["active_group"] = active_group
        context["is_owner"] = active_group.owner_id == self.request.user.id
        context["chat_url"] = reverse("student:messages") + f"?conversation={active_group.chat_conversation_id}"
        context["pending_invites"] = pending_invites
        context["group_saved_listings"] = (
            GroupSavedListing.objects
            .filter(group=active_group)
            .select_related("listing", "saved_by")
            .prefetch_related("listing__images")
        )
        return context


class GroupInviteView(BaseStudentGroupView, View):
    http_method_names = ["post", "head", "options"]

    def post(self, request, *args, **kwargs):
        group = get_object_or_404(
            Group.objects.select_related("owner", "chat_conversation"),
            id=kwargs["group_id"],
            memberships__user=request.user,
        )
        if group.owner_id != request.user.id:
            messages.error(request, "Only the group owner can invite members.")
            return redirect("groups:detail", group_id=group.id)

        invitee_id = request.POST.get("invitee_id")
        try:
            invitee = User.objects.get(id=int(invitee_id))
        except (TypeError, ValueError, User.DoesNotExist):
            messages.error(request, "Select a valid student to invite.")
            return redirect("groups:detail", group_id=group.id)

        if invitee.id == request.user.id:
            messages.error(request, "You are already in this group.")
            return redirect("groups:detail", group_id=group.id)

        if not Profile.objects.filter(user=invitee, user_type="student", email_verified=True).exists():
            messages.error(request, "Only verified student users can be invited.")
            return redirect("groups:detail", group_id=group.id)

        if GroupMembership.objects.filter(group=group, user=invitee).exists():
            messages.info(request, "This user is already a group member.")
            return redirect("groups:detail", group_id=group.id)

        pending_invite = GroupInvite.objects.filter(
            group=group,
            invitee=invitee,
            status=GroupInvite.Status.PENDING,
        ).first()
        if pending_invite:
            messages.info(request, "An invite is already pending for this user.")
            return redirect("groups:detail", group_id=group.id)

        invite = GroupInvite.objects.create(
            group=group,
            inviter=request.user,
            invitee=invitee,
        )
        dm = _find_or_create_dm(request.user, invitee)
        marker = f"[[GROUP_INVITE:{invite.id}]]"
        content = (
            f"{marker} {request.user.get_full_name() or request.user.username} invited you to "
            f'"{group.name}".'
        )
        Message.objects.create(conversation=dm, sender=request.user, content=content)
        dm.save(update_fields=["updated_at"])
        Notification.objects.create(
            recipient=invitee,
            kind="group_invite",
            title="New group invite",
            body=(
                f'{request.user.get_full_name() or request.user.username} invited you '
                f'to "{group.name}".'
            ),
            link_url=reverse("student:messages") + f"?conversation={dm.id}",
        )
        messages.success(request, "Invite sent in chat.")
        return redirect("groups:detail", group_id=group.id)


class GroupLeaveView(BaseStudentGroupView, View):
    http_method_names = ["post", "head", "options"]

    def post(self, request, *args, **kwargs):
        group = get_object_or_404(
            Group.objects.select_related("chat_conversation"),
            id=kwargs["group_id"],
            memberships__user=request.user,
        )
        if group.owner_id == request.user.id:
            messages.error(request, "Group owner cannot leave. Transfer ownership first.")
            return redirect("groups:detail", group_id=group.id)

        GroupMembership.objects.filter(group=group, user=request.user).delete()
        group.chat_conversation.participants.remove(request.user)
        messages.success(request, f'You left "{group.name}".')
        return redirect("groups:index")


class GroupDeleteView(BaseStudentGroupView, View):
    http_method_names = ["post", "head", "options"]

    def post(self, request, *args, **kwargs):
        group = get_object_or_404(
            Group.objects.select_related("chat_conversation"),
            id=kwargs["group_id"],
            memberships__user=request.user,
        )
        if group.owner_id != request.user.id:
            messages.error(request, "Only the group owner can delete this group.")
            return redirect("groups:detail", group_id=group.id)

        group_name = group.name
        conversation = group.chat_conversation
        group.delete()
        conversation.delete()
        messages.success(request, f'Group "{group_name}" and its chat were deleted.')
        return redirect("groups:index")


@login_required
@require_GET
def student_search(request):
    if not Profile.objects.filter(user=request.user, user_type="student").exists():
        return JsonResponse({"users": []})

    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"users": []})

    users = (
        User.objects.filter(
            profile__user_type="student",
            profile__email_verified=True,
        )
        .exclude(id=request.user.id)
        .filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(username__icontains=query)
        )[:20]
    )
    results = [
        {
            "id": u.id,
            "name": u.get_full_name() or u.username,
            "email": u.email,
        }
        for u in users
    ]
    return JsonResponse({"users": results})


@login_required
@require_POST
def accept_invite(request, invite_id):
    invite = get_object_or_404(
        GroupInvite.objects.select_related("group", "group__chat_conversation"),
        id=invite_id,
        invitee=request.user,
    )
    if invite.status != GroupInvite.Status.PENDING:
        return JsonResponse({"ok": False, "error": "Invite is no longer pending."}, status=400)

    if not Profile.objects.filter(user=request.user, user_type="student").exists():
        return JsonResponse({"ok": False, "error": "Only student users can join groups."}, status=403)

    GroupMembership.objects.get_or_create(group=invite.group, user=request.user)
    invite.group.chat_conversation.participants.add(request.user)
    invite.status = GroupInvite.Status.ACCEPTED
    invite.responded_at = timezone.now()
    invite.save(update_fields=["status", "responded_at"])
    invite.group.chat_conversation.save(update_fields=["updated_at"])
    Notification.objects.create(
        recipient=invite.group.owner,
        kind="group_invite",
        title="Group invite accepted",
        body=(
            f'{request.user.get_full_name() or request.user.username} accepted your invite '
            f'to "{invite.group.name}".'
        ),
        link_url="",
    )

    return JsonResponse(
        {
            "ok": True,
            "group_id": invite.group_id,
            "group_name": invite.group.name,
            "group_url": reverse("groups:detail", kwargs={"group_id": invite.group_id}),
            "conversation_id": invite.group.chat_conversation_id,
        }
    )


@login_required
@require_POST
def decline_invite(request, invite_id):
    invite = get_object_or_404(
        GroupInvite.objects.select_related("group"),
        id=invite_id,
        invitee=request.user,
    )
    if invite.status != GroupInvite.Status.PENDING:
        return JsonResponse({"ok": False, "error": "Invite is no longer pending."}, status=400)

    invite.status = GroupInvite.Status.DECLINED
    invite.responded_at = timezone.now()
    invite.save(update_fields=["status", "responded_at"])
    Notification.objects.create(
        recipient=invite.group.owner,
        kind="group_invite",
        title="Group invite declined",
        body=(
            f'{request.user.get_full_name() or request.user.username} declined your invite '
            f'to "{invite.group.name}".'
        ),
        link_url="",
    )

    return JsonResponse(
        {
            "ok": True,
            "group_id": invite.group_id,
            "group_name": invite.group.name,
            "invite_status": invite.status,
        }
    )


@login_required
@require_POST
def save_listing_to_group(request):
    if not Profile.objects.filter(user=request.user, user_type="student").exists():
        messages.error(request, "Only students can save listings to groups.")
        return redirect(request.POST.get("next") or "student:find_housing")

    next_url = request.POST.get("next") or reverse("student:find_housing")
    back_to_listings_url = (request.POST.get("back_to_listings_url") or "").strip()
    group_id = request.POST.get("group_id")
    listing_id = request.POST.get("listing_id")

    try:
        group = Group.objects.get(id=int(group_id), memberships__user=request.user)
        listing = Listing.objects.accessible_to(request.user).get(id=int(listing_id))
    except (TypeError, ValueError, Group.DoesNotExist, Listing.DoesNotExist):
        messages.error(request, "Unable to save this listing to group.")
        return redirect(next_url)

    _, created = GroupSavedListing.objects.get_or_create(
        group=group,
        listing=listing,
        defaults={"saved_by": request.user},
    )
    if created:
        messages.success(request, f'Saved "{listing.title}" to group "{group.name}".')
    else:
        messages.info(request, f'"{listing.title}" is already saved in "{group.name}".')

    if back_to_listings_url and url_has_allowed_host_and_scheme(
        url=back_to_listings_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        parsed = urllib.parse.urlsplit(next_url)
        query_items = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if not any(key == "back" for key, _ in query_items):
            query_items.append(("back", back_to_listings_url))
        next_url = urllib.parse.urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urllib.parse.urlencode(query_items),
                parsed.fragment,
            )
        )

    return redirect(next_url)


@login_required
@require_POST
def remove_listing_from_group(request):
    if not Profile.objects.filter(user=request.user, user_type="student").exists():
        messages.error(request, "Only students can remove group listings.")
        return redirect(request.POST.get("next") or reverse("student:find_housing"))

    next_url = request.POST.get("next") or reverse("groups:index")
    back_to_listings_url = (request.POST.get("back_to_listings_url") or "").strip()
    group_id = request.POST.get("group_id")
    listing_id = request.POST.get("listing_id")

    try:
        group = Group.objects.get(id=int(group_id), memberships__user=request.user)
        saved = GroupSavedListing.objects.select_related("listing").get(
            group=group,
            listing_id=int(listing_id),
        )
    except (TypeError, ValueError, Group.DoesNotExist, GroupSavedListing.DoesNotExist):
        messages.error(request, "Unable to remove this listing from the group.")
        return redirect(next_url)

    listing_title = saved.listing.title
    group_name = group.name
    saved.delete()
    messages.success(request, f'Removed "{listing_title}" from "{group_name}".')

    if back_to_listings_url and url_has_allowed_host_and_scheme(
        url=back_to_listings_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        parsed = urllib.parse.urlsplit(next_url)
        query_items = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if not any(key == "back" for key, _ in query_items):
            query_items.append(("back", back_to_listings_url))
        next_url = urllib.parse.urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urllib.parse.urlencode(query_items),
                parsed.fragment,
            )
        )

    return redirect(next_url)
