import random

from django.core.management.base import BaseCommand

from matching.models import Malumot
from matching.regions import REGIONS

PLATE_REGION_CODES = [
    "01", "10", "20", "25", "30", "40", "50", "60", "70", "75", "80", "85", "90", "95",
]
LETTERS = "ABCEHKMOPTXY"


def random_plate():
    code = random.choice(PLATE_REGION_CODES)
    a = random.choice(LETTERS)
    bc = "".join(random.choice(LETTERS) for _ in range(2))
    nums = random.randint(100, 999)
    return f"{code}{a}{nums}{bc}"


class Command(BaseCommand):
    help = "Tasodifiy transport vositalarini yaratadi"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=80)
        parser.add_argument("--clear", action="store_true")

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Malumot.objects.all().delete()
            self.stdout.write(f"Ochirildi: {deleted}")

        created = 0
        attempts = 0
        target = options["count"]
        while created < target and attempts < target * 5:
            attempts += 1
            region = random.choice(list(REGIONS.keys()))
            lat, lng = REGIONS[region]
            plate = random_plate()
            if Malumot.objects.filter(mashina_raqami=plate).exists():
                continue
            Malumot.objects.create(
                mashina_raqami=plate,
                joriy_hudud=region,
                joriy_lat=lat + random.uniform(-0.2, 0.2),
                joriy_lng=lng + random.uniform(-0.2, 0.2),
                is_available=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} ta mashina yaratildi"))
