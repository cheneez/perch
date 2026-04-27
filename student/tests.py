import json

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from listings.models import Listing, ListingImage


def _make_listing(owner, distance_miles, **kwargs):
    return Listing.objects.create(
        owner=owner,
        title=f'Listing {distance_miles}mi',
        address='123 Test St',
        price_monthly=1000,
        bedrooms=1,
        bathrooms=1,
        distance_miles=distance_miles,
        room_type='room',
        lease_type='full',
        status='available',
        latitude=42.33,
        longitude=-71.16,
        **kwargs,
    )


@override_settings(GOOGLE_MAPS_API_KEY='test-key')
class FindHousingViewTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.url = reverse('student:find_housing')

    def test_radius_filters_out_distant_listings(self):
        _make_listing(self.owner, distance_miles=0.5)
        _make_listing(self.owner, distance_miles=3.0)
        response = self.client.get(self.url, {'radius': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['listings'].count(), 1)
        self.assertEqual(float(response.context['listings'].first().distance_miles), 0.5)

    def test_default_radius_is_one_mile(self):
        _make_listing(self.owner, distance_miles=0.8)
        _make_listing(self.owner, distance_miles=1.5)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['listings'].count(), 1)

    def test_map_pins_include_url(self):
        _make_listing(self.owner, distance_miles=0.5)
        response = self.client.get(self.url)
        pins = json.loads(response.context['map_pins'])
        self.assertEqual(len(pins), 1)
        self.assertIn('/listings/property/', pins[0]['url'])

    def test_map_pins_include_primary_image_url(self):
        listing = _make_listing(self.owner, distance_miles=0.5)
        ListingImage.objects.create(
            listing=listing,
            image_url='https://example.com/house.jpg',
        )

        response = self.client.get(self.url)
        pins = json.loads(response.context['map_pins'])

        self.assertEqual(pins[0]['image_url'], 'https://example.com/house.jpg')

    def test_google_maps_key_in_context(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['google_maps_api_key'], 'test-key')

    def test_radius_in_context_matches_get_param(self):
        response = self.client.get(self.url, {'radius': '2'})
        self.assertEqual(response.context['radius'], '2')

    def test_invalid_radius_defaults_to_one(self):
        response = self.client.get(self.url, {'radius': 'bad'})
        self.assertEqual(response.context['radius'], '1')
