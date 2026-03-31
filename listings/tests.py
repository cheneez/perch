from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Listing


class ListingDetailAccessTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.owner = user_model.objects.create_user(
			username='owner',
			email='owner@example.com',
			password='password123',
		)
		self.listing = Listing.objects.create(
			owner=self.owner,
			title='Bright room near campus',
			description='Spacious room available now',
			address='123 College Ave',
			price_monthly='1500.00',
			room_type=Listing.RoomType.ROOM,
			lease_type=Listing.LeaseType.FULL,
		)

	def test_listing_detail_requires_login(self):
		url = reverse('listings:listing-detail', kwargs={'pk': self.listing.pk})
		response = self.client.get(url)
		self.assertEqual(response.status_code, 302)

	def test_listing_detail_accessible_by_owner(self):
		self.client.login(username='owner', password='password123')
		url = reverse('listings:listing-detail', kwargs={'pk': self.listing.pk})
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['listing'].pk, self.listing.pk)
		self.assertContains(response, self.listing.address)

	def test_legacy_property_route_is_public(self):
		url = reverse('listings:property', kwargs={'pk': self.listing.pk})
		response = self.client.get(url)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.context['listing'].pk, self.listing.pk)
		self.assertContains(response, self.listing.address)
