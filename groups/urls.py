from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    path("", views.GroupListView.as_view(), name="index"),
    path("save-listing/", views.save_listing_to_group, name="save_listing"),
    path("remove-listing/", views.remove_listing_from_group, name="remove_listing"),
    path("<int:group_id>/", views.GroupDetailView.as_view(), name="detail"),
    path("<int:group_id>/invite/", views.GroupInviteView.as_view(), name="invite"),
    path("<int:group_id>/delete/", views.GroupDeleteView.as_view(), name="delete"),
    path("<int:group_id>/leave/", views.GroupLeaveView.as_view(), name="leave"),
    path("api/students/search/", views.student_search, name="student_search"),
    path("api/invites/<int:invite_id>/accept/", views.accept_invite, name="accept_invite"),
    path("api/invites/<int:invite_id>/decline/", views.decline_invite, name="decline_invite"),
]
