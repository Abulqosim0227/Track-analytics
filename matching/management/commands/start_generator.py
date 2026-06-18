from django.core.management.base import BaseCommand

from matching.tasks import generate_zapros


class Command(BaseCommand):
    help = "Jonli zapros generatorini ishga tushiradi (Celery worker kerak)"

    def handle(self, *args, **options):
        result = generate_zapros.delay()
        self.stdout.write(
            self.style.SUCCESS(f"Generator ishga tushdi (task id: {result.id})")
        )
