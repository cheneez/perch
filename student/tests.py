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
        moderation_status='approved',
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

from django.test import TestCase
from django.urls import reverse

from accounts.models import Favorite, Profile
from student.compatibility import compatibility_percent
from student.models import StudentCompatibilitySurvey, StudentProfile


class FindRoommatesTests(TestCase):
    def _create_student(self, username, email=None, first_name="Test", last_name="User", verified=True):
        email = email or f"{username}@bc.edu"
        user = User.objects.create_user(
            username=username,
            email=email,
            password="securepass123",
            first_name=first_name,
            last_name=last_name,
        )
        Profile.objects.create(user=user, user_type="student", email_verified=verified)
        StudentProfile.objects.create(
            user=user,
            username=username,
            first_name=first_name,
            last_name=last_name,
            school="Boston College",
            grade_year="ug_senior",
            gender_identity="prefer_not",
        )
        return user

    def _create_survey(self, user, **overrides):
        payload = {
            "graduation_year": "2027",
            "major": "cs",
            "pets": "s3_depends",
            "smoking_habits": "s1_no_smoking",
            "party_at_home": "s2_rarely",
            "sleep_schedule": "s4_somewhat_early",
            "roommate_relationship": "s3_balanced",
            "morning_night_preference": "s5_morning_with_morning",
            "personality": "s3_in_between",
            "cleanliness": "s4_neat",
            "guests": "s2_sometimes",
            "noise_level": "s2_quiet",
            "study_at_home": "s4_often",
            "conflict_style": "s3_calm",
        }
        payload.update(overrides)
        return StudentCompatibilitySurvey.objects.create(user=user, **payload)

    def test_roommates_redirects_to_survey_when_incomplete(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        self.client.force_login(viewer)

        response = self.client.get(reverse("student:roommates"))

        self.assertRedirects(response, reverse("student:compatibility_survey"))

    def test_roommates_excludes_self_non_students_and_incomplete(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        self._create_survey(viewer)
        candidate = self._create_student("candidate", first_name="Alex", last_name="Rivera")
        self._create_survey(candidate, major="biology")

        incomplete = self._create_student("incomplete", first_name="No", last_name="Survey")

        lessor_user = User.objects.create_user(
            username="lessor1",
            email="lessor1@example.com",
            password="securepass123",
        )
        Profile.objects.create(user=lessor_user, user_type="realtor", email_verified=True)

        self.client.force_login(viewer)
        response = self.client.get(reverse("student:roommates"))

        self.assertEqual(response.status_code, 200)
        results = response.context["results"]
        ids = [item["user_id"] for item in results]
        self.assertIn(candidate.id, ids)
        self.assertNotIn(viewer.id, ids)
        self.assertNotIn(incomplete.id, ids)
        self.assertNotIn(lessor_user.id, ids)

    def test_roommates_include_admin_created_unverified_student_if_complete(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        self._create_survey(viewer)
        unverified_candidate = self._create_student(
            "adminmade",
            first_name="Admin",
            last_name="Made",
            verified=False,
        )
        self._create_survey(unverified_candidate)

        self.client.force_login(viewer)
        response = self.client.get(reverse("student:roommates"))

        ids = [item["user_id"] for item in response.context["results"]]
        self.assertIn(unverified_candidate.id, ids)

    def test_roommates_applies_hard_filters(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        self._create_survey(viewer, graduation_year="2027", major="cs")
        keep = self._create_student("keep", first_name="Chris", last_name="Stone")
        self._create_survey(keep, graduation_year="2027", major="cs", smoking_habits="s1_no_smoking")
        drop = self._create_student("drop", first_name="Pat", last_name="Liu")
        self._create_survey(drop, graduation_year="2026", major="biology", smoking_habits="s3_occasionally")

        self.client.force_login(viewer)
        response = self.client.get(
            reverse("student:roommates"),
            {"graduation_year": "2027", "major": "cs", "smoking_habits": "s1_no_smoking"},
        )

        ids = [item["user_id"] for item in response.context["results"]]
        self.assertEqual(ids, [keep.id])

    def test_roommates_filters_by_gender_identity(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        self._create_survey(viewer, graduation_year="2027", major="cs")
        woman_candidate = self._create_student("woman1", first_name="Alex", last_name="Rivera")
        woman_candidate.student_profile.gender_identity = "woman"
        woman_candidate.student_profile.save(update_fields=["gender_identity"])
        self._create_survey(woman_candidate, graduation_year="2027", major="cs")
        man_candidate = self._create_student("man1", first_name="Chris", last_name="Stone")
        man_candidate.student_profile.gender_identity = "man"
        man_candidate.student_profile.save(update_fields=["gender_identity"])
        self._create_survey(man_candidate, graduation_year="2027", major="cs")

        self.client.force_login(viewer)
        response = self.client.get(reverse("student:roommates"), {"gender_identity": "woman"})

        ids = [item["user_id"] for item in response.context["results"]]
        self.assertEqual(ids, [woman_candidate.id])

    def test_roommates_context_marks_favorited_profiles(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        self._create_survey(viewer)
        keep = self._create_student("keep", first_name="Chris", last_name="Stone")
        self._create_survey(keep)
        other = self._create_student("other", first_name="Pat", last_name="Liu")
        self._create_survey(other)
        Favorite.objects.create(user=viewer, favorited_user=keep)

        self.client.force_login(viewer)
        response = self.client.get(reverse("student:roommates"))

        favorite_flags = {
            item["user_id"]: item["is_favorited"] for item in response.context["results"]
        }
        self.assertTrue(favorite_flags[keep.id])
        self.assertFalse(favorite_flags[other.id])

    def test_roommates_favorites_only_shows_favorited_only(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        self._create_survey(viewer)
        favorite_user = self._create_student("fav", first_name="Fav", last_name="User")
        self._create_survey(favorite_user)
        other = self._create_student("other", first_name="Other", last_name="User")
        self._create_survey(other)
        Favorite.objects.create(user=viewer, favorited_user=favorite_user)

        self.client.force_login(viewer)
        response = self.client.get(reverse("student:roommates"), {"favorites_only": "1"})

        ids = [item["user_id"] for item in response.context["results"]]
        self.assertEqual(ids, [favorite_user.id])
        self.assertTrue(response.context["favorites_only"])

    def test_public_profile_favorite_toggle_redirects_to_safe_next(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        target = self._create_student("target", first_name="Alex", last_name="Rivera")

        self.client.force_login(viewer)
        next_url = reverse("student:roommates") + "?gender_identity=woman"
        response = self.client.post(
            reverse("student:public_profile_favorite", kwargs={"user_id": target.id}),
            {"next": next_url},
        )

        self.assertRedirects(response, next_url, fetch_redirect_response=False)
        self.assertTrue(
            Favorite.objects.filter(user=viewer, favorited_user=target).exists()
        )

    def test_compatibility_percent_orders_closest_match_first(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        viewer_survey = self._create_survey(viewer)
        close = self._create_student("close", first_name="Taylor", last_name="Ng")
        close_survey = self._create_survey(close)
        far = self._create_student("far", first_name="Jordan", last_name="Khan")
        far_survey = self._create_survey(
            far,
            smoking_habits="s5_doesnt_matter",
            cleanliness="s1_messy",
            noise_level="s5_very_lively",
            sleep_schedule="s1_night_owl",
        )

        close_score = compatibility_percent(viewer_survey, close_survey)
        far_score = compatibility_percent(viewer_survey, far_survey)
        self.assertGreaterEqual(close_score, far_score)

        self.client.force_login(viewer)
        response = self.client.get(reverse("student:roommates"))
        ids = [item["user_id"] for item in response.context["results"]]
        self.assertEqual(ids[0], close.id)

    def test_profile_find_roommates_link_points_to_survey_until_completed(self):
        viewer = self._create_student("viewer", first_name="Jorge", last_name="Mendez")
        self.client.force_login(viewer)

        response = self.client.get(reverse("student:profile"))
        self.assertContains(response, reverse("student:compatibility_survey"))

        self._create_survey(viewer)
        response = self.client.get(reverse("student:profile"))
        self.assertContains(response, reverse("student:roommates"))
