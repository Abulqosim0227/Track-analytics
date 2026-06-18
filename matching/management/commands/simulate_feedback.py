import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from matching.models import AgentTaklif


class Command(BaseCommand):
    help = "Mavjud takliflarga baholash (feedback) simulyatsiya qiladi"

    def add_arguments(self, parser):
        parser.add_argument("--coverage", type=float, default=0.85)
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **options):
        if options["reset"]:
            AgentTaklif.objects.update(
                feedback=AgentTaklif.FEEDBACK_PENDING, feedback_at=None
            )

        coverage = options["coverage"]
        now = timezone.now()
        accepted = 0
        rejected = 0

        for taklif in AgentTaklif.objects.select_related("zapros", "mashina"):
            if random.random() > coverage:
                continue

            same_region = (
                taklif.mashina.joriy_hudud == taklif.zapros.yuk_ortish_joyi
            )
            close = taklif.masofa_km is not None and taklif.masofa_km < 80
            good_match = same_region or close

            accept_prob = 0.9 if good_match else 0.3
            if random.random() < accept_prob:
                taklif.feedback = AgentTaklif.FEEDBACK_ACCEPTED
                accepted += 1
            else:
                taklif.feedback = AgentTaklif.FEEDBACK_REJECTED
                rejected += 1
            taklif.feedback_at = now
            taklif.save(update_fields=["feedback", "feedback_at", "updated_at"])

        total = accepted + rejected
        acc = round(accepted / total * 100, 1) if total else 0
        self.stdout.write(
            self.style.SUCCESS(
                f"Baholandi: {total} (qabul {accepted}, rad {rejected}), aniqlik {acc}%"
            )
        )
