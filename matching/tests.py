from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import AgentTaklif, Malumot, Zapros
from .services.geo import haversine_km, score_candidate
from .services.matcher import build_shortlist, run_match


class GeoTests(TestCase):
    def test_haversine_known_distance(self):
        d = haversine_km(41.2995, 69.2401, 39.6270, 66.9750)
        self.assertTrue(250 < d < 320)

    def test_haversine_missing_coords(self):
        self.assertIsNone(haversine_km(None, 1, 2, 3))

    def test_same_region_scores_higher_than_far(self):
        same = Malumot(joriy_hudud="Toshkent", joriy_lat=41.3, joriy_lng=69.2)
        far = Malumot(joriy_hudud="Xorazm", joriy_lat=41.5, joriy_lng=60.6)
        same_score, _ = score_candidate("Toshkent", 41.2995, 69.2401, same)
        far_score, _ = score_candidate("Toshkent", 41.2995, 69.2401, far)
        self.assertGreater(same_score, far_score)


class ShortlistTests(TestCase):
    def setUp(self):
        Malumot.objects.create(
            mashina_raqami="01A111BC", joriy_hudud="Toshkent",
            joriy_lat=41.3, joriy_lng=69.2,
        )
        Malumot.objects.create(
            mashina_raqami="95X999YZ", joriy_hudud="Xorazm",
            joriy_lat=41.5, joriy_lng=60.6,
        )
        Malumot.objects.create(
            mashina_raqami="10B222CE", joriy_hudud="Samarqand",
            joriy_lat=39.6, joriy_lng=66.9, is_available=False,
        )

    def test_shortlist_excludes_unavailable_and_ranks_nearest_first(self):
        zapros = Zapros.objects.create(
            yuk_ortish_joyi="Toshkent", yuk_ortish_lat=41.2995,
            yuk_ortish_lng=69.2401, yuk_tushirish_joyi="Samarqand",
            yuklash_sanasi=timezone.now().date(),
        )
        shortlist = build_shortlist(zapros)
        plates = [v.mashina_raqami for _, _, v in shortlist]
        self.assertNotIn("10B222CE", plates)
        self.assertEqual(plates[0], "01A111BC")


@override_settings(LLM_API_KEY="")
class RunMatchTests(TestCase):
    def setUp(self):
        Malumot.objects.create(
            mashina_raqami="01A111BC", joriy_hudud="Toshkent",
            joriy_lat=41.3, joriy_lng=69.2,
        )

    def test_run_match_without_llm_uses_fallback(self):
        zapros = Zapros.objects.create(
            yuk_ortish_joyi="Toshkent", yuk_ortish_lat=41.2995,
            yuk_ortish_lng=69.2401, yuk_tushirish_joyi="Samarqand",
            yuklash_sanasi=timezone.now().date(),
        )
        taklif = run_match(zapros.id)
        self.assertIsNotNone(taklif)
        zapros.refresh_from_db()
        self.assertEqual(zapros.status, Zapros.STATUS_MATCHED)
        self.assertEqual(taklif.mashina.mashina_raqami, "01A111BC")
        self.assertGreaterEqual(taklif.latency_ms, 0)

    def test_run_match_no_vehicles(self):
        Malumot.objects.all().delete()
        zapros = Zapros.objects.create(
            yuk_ortish_joyi="Toshkent", yuk_ortish_lat=41.2995,
            yuk_ortish_lng=69.2401, yuk_tushirish_joyi="Samarqand",
            yuklash_sanasi=timezone.now().date(),
        )
        self.assertIsNone(run_match(zapros.id))
        zapros.refresh_from_db()
        self.assertEqual(zapros.status, Zapros.STATUS_NO_MATCH)


class LlmPickTests(TestCase):
    def setUp(self):
        Malumot.objects.create(
            mashina_raqami="01A111BC", joriy_hudud="Toshkent",
            joriy_lat=41.3, joriy_lng=69.2,
        )

    @override_settings(LLM_API_KEY="test-key")
    @patch("matching.services.matcher._llm_pick")
    def test_run_match_uses_llm_choice(self, mock_pick):
        mock_pick.return_value = ("01A111BC", "LLM tanlovi")
        zapros = Zapros.objects.create(
            yuk_ortish_joyi="Toshkent", yuk_ortish_lat=41.2995,
            yuk_ortish_lng=69.2401, yuk_tushirish_joyi="Samarqand",
            yuklash_sanasi=timezone.now().date(),
        )
        taklif = run_match(zapros.id)
        self.assertEqual(taklif.agent_izohi, "LLM tanlovi")
        mock_pick.assert_called_once()


@override_settings(LLM_API_KEY="")
class DashboardTests(TestCase):
    def test_dashboard_renders_with_data(self):
        Malumot.objects.create(
            mashina_raqami="01A111BC", joriy_hudud="Toshkent",
            joriy_lat=41.3, joriy_lng=69.2,
        )
        zapros = Zapros.objects.create(
            yuk_ortish_joyi="Toshkent", yuk_ortish_lat=41.2995,
            yuk_ortish_lng=69.2401, yuk_tushirish_joyi="Samarqand",
            yuklash_sanasi=timezone.now().date(),
        )
        run_match(zapros.id)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Freight Matching")
        self.assertContains(response, "01A111BC")

    def test_dashboard_renders_empty(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)


@override_settings(LLM_API_KEY="")
class FeedbackTests(TestCase):
    def setUp(self):
        Malumot.objects.create(
            mashina_raqami="01A111BC", joriy_hudud="Toshkent",
            joriy_lat=41.3, joriy_lng=69.2,
        )
        zapros = Zapros.objects.create(
            yuk_ortish_joyi="Toshkent", yuk_ortish_lat=41.2995,
            yuk_ortish_lng=69.2401, yuk_tushirish_joyi="Samarqand",
            yuklash_sanasi=timezone.now().date(),
        )
        self.taklif = run_match(zapros.id)

    def test_submit_feedback_updates_and_redirects(self):
        url = reverse("submit_feedback", args=[self.taklif.id])
        response = self.client.post(url, {"feedback": "accepted"})
        self.assertEqual(response.status_code, 302)
        self.taklif.refresh_from_db()
        self.assertEqual(self.taklif.feedback, AgentTaklif.FEEDBACK_ACCEPTED)
        self.assertIsNotNone(self.taklif.feedback_at)

    def test_submit_feedback_rejects_invalid_value(self):
        url = reverse("submit_feedback", args=[self.taklif.id])
        self.client.post(url, {"feedback": "garbage"})
        self.taklif.refresh_from_db()
        self.assertEqual(self.taklif.feedback, AgentTaklif.FEEDBACK_PENDING)

    def test_dashboard_shows_accuracy(self):
        self.taklif.feedback = AgentTaklif.FEEDBACK_ACCEPTED
        self.taklif.feedback_at = timezone.now()
        self.taklif.save()
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Aniqlik")
        self.assertContains(response, "100.0")
