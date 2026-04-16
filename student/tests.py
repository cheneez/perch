from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
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
