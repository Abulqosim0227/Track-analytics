import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from matching.models import AgentTaklif, Zapros
from matching.regions import REGIONS
from matching.services.matcher import build_shortlist


class Command(BaseCommand):
    help = "Tasodifiy zaproslarni vaqt boyicha taqsimlab yaratadi"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=400)
        parser.add_argument("--hours", type=int, default=24)
        parser.add_argument("--clear", action="store_true")
        parser.add_argument(
            "--match",
            action="store_true",
            help="Algoritmik moslashtirishni simulyatsiya qiladi (LLM chaqirilmaydi)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            AgentTaklif.objects.all().delete()
            deleted, _ = Zapros.objects.all().delete()
            self.stdout.write(f"Ochirildi: {deleted} zapros")

        count = options["count"]
        window = timedelta(hours=options["hours"])
        now = timezone.now()
        regions = list(REGIONS.keys())

        created = []
        for _ in range(count):
            pickup = random.choice(regions)
            dropoff = random.choice([r for r in regions if r != pickup])
            lat, lng = REGIONS[pickup]
            zapros = Zapros.objects.create(
                yuk_ortish_joyi=pickup,
                yuk_ortish_lat=lat + random.uniform(-0.15, 0.15),
                yuk_ortish_lng=lng + random.uniform(-0.15, 0.15),
                yuk_tushirish_joyi=dropoff,
                yuklash_sanasi=now.date() + timedelta(days=random.randint(0, 3)),
            )
            offset = window * random.random()
            created_at = now - offset
            Zapros.objects.filter(pk=zapros.pk).update(created_at=created_at)
            zapros.created_at = created_at
            created.append(zapros)

        self.stdout.write(self.style.SUCCESS(f"{len(created)} ta zapros yaratildi"))

        if not options["match"]:
            return

        matched = 0
        for zapros in created:
            shortlist = build_shortlist(zapros)
            if not shortlist:
                zapros.status = Zapros.STATUS_NO_MATCH
                zapros.save(update_fields=["status"])
                continue
            score, distance, vehicle = shortlist[0]
            latency_ms = random.randint(400, 5000)
            taklif_vaqti = zapros.created_at + timedelta(milliseconds=latency_ms)
            AgentTaklif.objects.create(
                zapros=zapros,
                mashina=vehicle,
                reyting_ball=score,
                masofa_km=distance,
                agent_izohi="Simulyatsiya: algoritmik eng yuqori reyting.",
                zapros_yaratilgan_vaqti=zapros.created_at,
                agent_taklif_bergan_vaqti=taklif_vaqti,
                latency_ms=latency_ms,
            )
            zapros.status = Zapros.STATUS_MATCHED
            zapros.save(update_fields=["status"])
            matched += 1

        self.stdout.write(self.style.SUCCESS(f"{matched} ta zapros moslashtirildi"))
