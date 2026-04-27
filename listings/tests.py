import json
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from listings.models import Listing
from listings.views import _distance_miles_from_bc, _google_geocode


class GoogleGeocodeTests(TestCase):
    @override_settings(GOOGLE_MAPS_API_KEY='test-key')
    @patch('listings.views.urllib.request.urlopen')
    def test_google_geocode_returns_lat_lng_from_google_response(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({
            'status': 'OK',
            'results': [
                {
                    'geometry': {
                        'location': {
                            'lat': 42.3391,
                            'lng': -71.1672,
                        }
                    }
                }
            ],
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = response

        lat, lng = _google_geocode('25 Commonwealth Ave, Brighton, MA 02135')

        self.assertEqual((lat, lng), (42.3391, -71.1672))

    @override_settings(GOOGLE_MAPS_API_KEY='test-key')
    @patch('listings.views.urllib.request.urlopen')
    def test_google_geocode_returns_none_when_google_does_not_match(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({
            'status': 'ZERO_RESULTS',
            'results': [],
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = response

        lat, lng = _google_geocode('not a real address')

        self.assertEqual((lat, lng), (None, None))


class CreateListingCoordinatesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='realtor_seed',
            email='realtor@perch.dev',
            password='perch1234',
        )
        self.client.force_login(self.user)

    def _post_data(self, **overrides):
        data = {
            'title': 'Sunny 2BR Near Boston College',
            'description': 'Bright apartment close to campus.',
            'address': '25 Commonwealth Ave, Brighton, MA 02135',
            'price_monthly': '2400.00',
            'bedrooms': '2',
            'bathrooms': '1',
            'distance_miles': '0.40',
            'room_type': Listing.RoomType.WHOLE_APARTMENT,
            'lease_type': Listing.LeaseType.FULL,
            'status': Listing.Status.AVAILABLE,
        }
        data.update(overrides)
        return data

    def test_create_listing_uses_coordinates_from_google_places_submission(self):
        response = self.client.post(reverse('listings:listings-create'), data=self._post_data(
            _lat='42.3391',
            _lng='-71.1672',
        ))

        self.assertRedirects(response, reverse('listings:listing-detail', args=[1]))
        listing = Listing.objects.get()
        self.assertEqual((listing.latitude, listing.longitude), (42.3391, -71.1672))
        self.assertEqual(listing.distance_miles, round(_distance_miles_from_bc(42.3391, -71.1672), 2))

    @override_settings(GOOGLE_MAPS_API_KEY='test-key')
    @patch('listings.views.urllib.request.urlopen')
    def test_create_listing_falls_back_to_google_geocode_when_hidden_coordinates_missing(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({
            'status': 'OK',
            'results': [
                {
                    'geometry': {
                        'location': {
                            'lat': 42.3391,
                            'lng': -71.1672,
                        }
                    }
                }
            ],
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = response

        self.client.post(reverse('listings:listings-create'), data=self._post_data())

        listing = Listing.objects.get()
        self.assertEqual((listing.latitude, listing.longitude), (42.3391, -71.1672))
        self.assertEqual(listing.distance_miles, round(_distance_miles_from_bc(42.3391, -71.1672), 2))
