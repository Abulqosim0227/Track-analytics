from django.contrib import admin

from .models import AgentTaklif, Malumot, Zapros


@admin.register(Zapros)
class ZaprosAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "yuk_ortish_joyi",
        "yuk_tushirish_joyi",
        "yuklash_sanasi",
        "status",
        "created_at",
    )
    list_filter = ("status", "yuk_ortish_joyi")
    search_fields = ("id",)


@admin.register(Malumot)
class MalumotAdmin(admin.ModelAdmin):
    list_display = ("id", "mashina_raqami", "joriy_hudud", "is_available")
    list_filter = ("is_available", "joriy_hudud")
    search_fields = ("mashina_raqami",)


@admin.register(AgentTaklif)
class AgentTaklifAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "zapros",
        "mashina",
        "reyting_ball",
        "masofa_km",
        "latency_ms",
        "feedback",
        "created_at",
    )
    list_filter = ("feedback", "created_at")
    search_fields = ("zapros__id", "mashina__mashina_raqami")
