from datetime import timedelta

from django.db.models import Avg, Count, Max, Min
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import AgentTaklif, Malumot, Zapros


def _percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    k = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[k]


def dashboard(request):
    now = timezone.now()
    day_ago = now - timedelta(hours=24)

    total = Zapros.objects.count()
    matched = Zapros.objects.filter(status=Zapros.STATUS_MATCHED).count()
    no_match = Zapros.objects.filter(status=Zapros.STATUS_NO_MATCH).count()
    pending = Zapros.objects.filter(status=Zapros.STATUS_NEW).count()
    match_rate = round(matched / total * 100, 1) if total else 0.0

    latency_stats = AgentTaklif.objects.aggregate(
        avg=Avg("latency_ms"), min=Min("latency_ms"), max=Max("latency_ms")
    )
    latency_values = list(
        AgentTaklif.objects.values_list("latency_ms", flat=True)
    )
    p95 = _percentile(latency_values, 95)

    avg_distance = AgentTaklif.objects.aggregate(avg=Avg("masofa_km"))["avg"]

    taklif_total = AgentTaklif.objects.count()
    fb_accepted = AgentTaklif.objects.filter(
        feedback=AgentTaklif.FEEDBACK_ACCEPTED
    ).count()
    fb_rejected = AgentTaklif.objects.filter(
        feedback=AgentTaklif.FEEDBACK_REJECTED
    ).count()
    fb_total = fb_accepted + fb_rejected
    accuracy = round(fb_accepted / fb_total * 100, 1) if fb_total else None
    coverage = round(fb_total / taklif_total * 100, 1) if taklif_total else 0.0

    vehicles_total = Malumot.objects.count()
    vehicles_available = Malumot.objects.filter(is_available=True).count()

    per_hour = []
    max_hour_count = 1
    for i in range(23, -1, -1):
        start = now - timedelta(hours=i + 1)
        end = now - timedelta(hours=i)
        count = Zapros.objects.filter(
            created_at__gte=start, created_at__lt=end
        ).count()
        max_hour_count = max(max_hour_count, count)
        per_hour.append({"label": end.strftime("%H:00"), "count": count})
    for row in per_hour:
        row["pct"] = round(row["count"] / max_hour_count * 100)

    top_regions = list(
        Zapros.objects.values("yuk_ortish_joyi")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    max_region_count = max((r["count"] for r in top_regions), default=1)
    for row in top_regions:
        row["pct"] = round(row["count"] / max_region_count * 100)

    recent = (
        AgentTaklif.objects.select_related("zapros", "mashina")
        .order_by("-created_at")[:20]
    )

    context = {
        "total": total,
        "matched": matched,
        "no_match": no_match,
        "pending": pending,
        "match_rate": match_rate,
        "latency_avg": round(latency_stats["avg"]) if latency_stats["avg"] else None,
        "latency_min": latency_stats["min"],
        "latency_max": latency_stats["max"],
        "latency_p95": p95,
        "avg_distance": round(avg_distance, 1) if avg_distance else None,
        "accuracy": accuracy,
        "fb_accepted": fb_accepted,
        "fb_rejected": fb_rejected,
        "fb_coverage": coverage,
        "vehicles_total": vehicles_total,
        "vehicles_available": vehicles_available,
        "requests_24h": sum(r["count"] for r in per_hour),
        "per_hour": per_hour,
        "top_regions": top_regions,
        "recent": recent,
        "generated_at": now,
    }
    return render(request, "matching/dashboard.html", context)


@require_POST
def submit_feedback(request, taklif_id):
    value = request.POST.get("feedback")
    valid = {AgentTaklif.FEEDBACK_ACCEPTED, AgentTaklif.FEEDBACK_REJECTED}
    if value in valid:
        AgentTaklif.objects.filter(pk=taklif_id).update(
            feedback=value, feedback_at=timezone.now()
        )
    return redirect("dashboard")
