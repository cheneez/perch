from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.urls import reverse


class PerchAdminSite(AdminSite):
    site_header = 'Perch Admin'
    site_title = 'Perch Admin'
    index_title = 'Moderation Dashboard'

    def index(self, request, extra_context=None):
        from accounts.models import Profile
        from listings.models import Listing
        from moderation.models import Report

        extra_context = extra_context or {}
        extra_context['dashboard_stats'] = [
            {
                'label': 'Advertised listings',
                'value': Listing.objects.filter(
                    moderation_status=Listing.ModerationStatus.APPROVED
                ).count(),
                'link': f"{reverse('admin:listings_listing_changelist')}?moderation_status__exact=approved",
            },
            {
                'label': 'Pending approval',
                'value': Listing.objects.filter(
                    moderation_status=Listing.ModerationStatus.PENDING
                ).count(),
                'link': f"{reverse('admin:listings_listing_changelist')}?moderation_status__exact=pending",
            },
            {
                'label': 'Rejected listings',
                'value': Listing.objects.filter(
                    moderation_status=Listing.ModerationStatus.REJECTED
                ).count(),
                'link': f"{reverse('admin:listings_listing_changelist')}?moderation_status__exact=rejected",
            },
            {
                'label': 'Rented / leased',
                'value': Listing.objects.filter(status=Listing.Status.RENTED).count(),
                'link': f"{reverse('admin:listings_listing_changelist')}?status__exact=rented",
            },
            {
                'label': 'Open reports',
                'value': Report.objects.filter(status=Report.Status.OPEN).count(),
                'link': f"{reverse('admin:moderation_report_changelist')}?status__exact=open",
            },
            {
                'label': 'Suspended users',
                'value': Profile.objects.filter(
                    account_status=Profile.AccountStatus.SUSPENDED
                ).count(),
                'link': f"{reverse('admin:accounts_profile_changelist')}?account_status__exact=suspended",
            },
        ]
        extra_context['dashboard_quick_access'] = [
            {
                'title': 'People & accounts',
                'items': [
                    {
                        'label': 'Users',
                        'admin_url': reverse('admin:auth_user_changelist'),
                        'add_url': reverse('admin:auth_user_add'),
                    },
                    {
                        'label': 'Profiles',
                        'admin_url': reverse('admin:accounts_profile_changelist'),
                        'add_url': reverse('admin:accounts_profile_add'),
                    },
                    {
                        'label': 'Favorites',
                        'admin_url': reverse('admin:accounts_favorite_changelist'),
                        'add_url': reverse('admin:accounts_favorite_add'),
                    },
                    {
                        'label': 'Student profiles',
                        'admin_url': reverse('admin:student_studentprofile_changelist'),
                        'add_url': reverse('admin:student_studentprofile_add'),
                    },
                    {
                        'label': 'Lessor profiles',
                        'admin_url': reverse('admin:lessor_lessorprofile_changelist'),
                        'add_url': reverse('admin:lessor_lessorprofile_add'),
                    },
                    {
                        'label': 'Groups',
                        'admin_url': reverse('admin:auth_group_changelist'),
                        'add_url': reverse('admin:auth_group_add'),
                    },
                ],
            },
            {
                'title': 'Listings',
                'items': [
                    {
                        'label': 'Listings',
                        'admin_url': reverse('admin:listings_listing_changelist'),
                        'add_url': reverse('admin:listings_listing_add'),
                    },
                    {
                        'label': 'Listing images',
                        'admin_url': reverse('admin:listings_listingimage_changelist'),
                        'add_url': reverse('admin:listings_listingimage_add'),
                    },
                ],
            },
            {
                'title': 'Moderation',
                'items': [
                    {
                        'label': 'Reports',
                        'admin_url': reverse('admin:moderation_report_changelist'),
                        'add_url': None,
                    },
                ],
            },
        ]
        return super().index(request, extra_context)


class PerchAdminConfig(AdminConfig):
    default_site = 'perch.admin.PerchAdminSite'
