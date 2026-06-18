import json
import logging
import re

from django.conf import settings
from django.utils import timezone

from ..models import AgentTaklif, Malumot, Zapros
from .geo import score_candidate

logger = logging.getLogger(__name__)


def _parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def build_shortlist(zapros, limit=None):
    limit = limit or settings.MATCHER_SHORTLIST_SIZE
    vehicles = Malumot.objects.filter(is_available=True)
    scored = []
    for vehicle in vehicles:
        score, distance = score_candidate(
            zapros.yuk_ortish_joyi,
            zapros.yuk_ortish_lat,
            zapros.yuk_ortish_lng,
            vehicle,
        )
        scored.append((score, distance, vehicle))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:limit]


def _llm_pick(zapros, shortlist):
    from openai import OpenAI

    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)

    lines = []
    for score, distance, vehicle in shortlist:
        dist_text = f"{distance:.0f} km" if distance is not None else "nomalum"
        lines.append(
            f"- {vehicle.mashina_raqami}: hudud={vehicle.joriy_hudud}, "
            f"masofa={dist_text}, reyting={score:.1f}"
        )
    candidates_text = "\n".join(lines)

    prompt = (
        "Yuk tashish uchun eng mos mashinani tanla.\n\n"
        f"Yuk ortish joyi: {zapros.yuk_ortish_joyi}\n"
        f"Yuk tushirish joyi: {zapros.yuk_tushirish_joyi}\n\n"
        f"Mavjud mashinalar:\n{candidates_text}\n\n"
        "Eng yaqin va eng mos mashinani tanla. Javobni faqat JSON formatda "
        'qaytar: {"mashina_raqami": "...", "izoh": "..."}. '
        "mashina_raqami royxatdagilardan biri bolishi shart."
    )

    response = client.chat.completions.create(
        model=settings.MATCHER_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    data = _parse_json(response.choices[0].message.content)
    return data["mashina_raqami"], data["izoh"]


def run_match(zapros_id):
    zapros = Zapros.objects.get(pk=zapros_id)
    shortlist = build_shortlist(zapros)

    if not shortlist:
        zapros.status = Zapros.STATUS_NO_MATCH
        zapros.save(update_fields=["status", "updated_at"])
        logger.warning("Zapros %s uchun mos mashina topilmadi", zapros_id)
        return None

    by_number = {v.mashina_raqami: (s, d, v) for s, d, v in shortlist}
    chosen_number = None
    izoh = ""

    if settings.LLM_API_KEY:
        try:
            chosen_number, izoh = _llm_pick(zapros, shortlist)
        except Exception as exc:
            logger.error("LLM pick xatosi, fallback ishlatiladi: %s", exc)

    if chosen_number not in by_number:
        score, distance, vehicle = shortlist[0]
        izoh = izoh or "Algoritmik tanlov: eng yuqori reytingli mashina."
    else:
        score, distance, vehicle = by_number[chosen_number]

    now = timezone.now()
    latency_ms = int((now - zapros.created_at).total_seconds() * 1000)

    taklif = AgentTaklif.objects.create(
        zapros=zapros,
        mashina=vehicle,
        reyting_ball=score,
        masofa_km=distance,
        agent_izohi=izoh,
        zapros_yaratilgan_vaqti=zapros.created_at,
        agent_taklif_bergan_vaqti=now,
        latency_ms=latency_ms,
    )

    zapros.status = Zapros.STATUS_MATCHED
    zapros.save(update_fields=["status", "updated_at"])

    logger.info(
        "Zapros %s -> mashina %s (latency %s ms)",
        zapros_id,
        vehicle.mashina_raqami,
        latency_ms,
    )
    return taklif
