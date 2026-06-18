import logging
import random
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Zapros
from .regions import REGIONS
from .services.matcher import run_match

logger = logging.getLogger(__name__)


def _jitter_coord(value, spread=0.15):
    return value + random.uniform(-spread, spread)


def create_random_zapros():
    pickup = random.choice(list(REGIONS.keys()))
    dropoff = random.choice([r for r in REGIONS if r != pickup])
    lat, lng = REGIONS[pickup]
    load_date = timezone.now().date() + timedelta(days=random.randint(0, 3))

    return Zapros.objects.create(
        yuk_ortish_joyi=pickup,
        yuk_ortish_lat=_jitter_coord(lat),
        yuk_ortish_lng=_jitter_coord(lng),
        yuk_tushirish_joyi=dropoff,
        yuklash_sanasi=load_date,
    )


@shared_task
def match_zapros(zapros_id):
    return bool(run_match(zapros_id))


@shared_task
def generate_zapros():
    zapros = create_random_zapros()
    match_zapros.delay(zapros.id)

    today = timezone.now().date()
    count_today = Zapros.objects.filter(created_at__date=today).count()
    logger.info("Yangi zapros #%s yaratildi (bugun jami: %s)", zapros.id, count_today)

    delay_minutes = random.uniform(
        settings.GENERATOR_MIN_MINUTES, settings.GENERATOR_MAX_MINUTES
    )
    generate_zapros.apply_async(countdown=int(delay_minutes * 60))
    return zapros.id
