from django.core.management.base import BaseCommand

from matching.services.matcher import run_match
from matching.tasks import create_random_zapros


class Command(BaseCommand):
    help = "Jonli generator: yangi zaproslar yaratib real LLM agent bilan moslashtiradi"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=20)

    def handle(self, *args, **options):
        count = options["count"]
        matched = 0
        for i in range(count):
            zapros = create_random_zapros()
            taklif = run_match(zapros.id)
            if taklif:
                matched += 1
                self.stdout.write(
                    f"[{i + 1}/{count}] zapros #{zapros.id} "
                    f"{zapros.yuk_ortish_joyi} -> {taklif.mashina.mashina_raqami} "
                    f"({taklif.latency_ms} ms)"
                )
            else:
                self.stdout.write(f"[{i + 1}/{count}] zapros #{zapros.id} mos topilmadi")

        self.stdout.write(
            self.style.SUCCESS(f"{matched}/{count} ta zapros moslashtirildi")
        )
