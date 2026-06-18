from django.db import models

from .regions import REGION_NAMES

REGION_CHOICES = [(name, name) for name in REGION_NAMES]


class Zapros(models.Model):
    STATUS_NEW = "new"
    STATUS_MATCHED = "matched"
    STATUS_NO_MATCH = "no_match"
    STATUS_CHOICES = [
        (STATUS_NEW, "Yangi"),
        (STATUS_MATCHED, "Tavsiya berildi"),
        (STATUS_NO_MATCH, "Mos mashina yoq"),
    ]

    yuk_ortish_joyi = models.CharField(max_length=64, choices=REGION_CHOICES)
    yuk_ortish_lat = models.FloatField(null=True, blank=True)
    yuk_ortish_lng = models.FloatField(null=True, blank=True)
    yuk_tushirish_joyi = models.CharField(max_length=64, choices=REGION_CHOICES)
    yuklash_sanasi = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "zaproslar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["yuk_ortish_joyi"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"#{self.pk} {self.yuk_ortish_joyi} -> {self.yuk_tushirish_joyi}"


class Malumot(models.Model):
    mashina_raqami = models.CharField(max_length=16, unique=True)
    joriy_hudud = models.CharField(max_length=64, choices=REGION_CHOICES)
    joriy_lat = models.FloatField(null=True, blank=True)
    joriy_lng = models.FloatField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "malumotlar"
        ordering = ["mashina_raqami"]
        indexes = [
            models.Index(fields=["joriy_hudud"]),
            models.Index(fields=["is_available"]),
        ]

    def __str__(self):
        return f"{self.mashina_raqami} ({self.joriy_hudud})"


class AgentTaklif(models.Model):
    FEEDBACK_PENDING = "pending"
    FEEDBACK_ACCEPTED = "accepted"
    FEEDBACK_REJECTED = "rejected"
    FEEDBACK_CHOICES = [
        (FEEDBACK_PENDING, "Baholanmagan"),
        (FEEDBACK_ACCEPTED, "Qabul qilindi"),
        (FEEDBACK_REJECTED, "Rad etildi"),
    ]

    zapros = models.ForeignKey(
        Zapros, on_delete=models.CASCADE, related_name="takliflar"
    )
    mashina = models.ForeignKey(
        Malumot, on_delete=models.CASCADE, related_name="takliflar"
    )
    reyting_ball = models.FloatField()
    masofa_km = models.FloatField(null=True, blank=True)
    agent_izohi = models.TextField(blank=True)
    zapros_yaratilgan_vaqti = models.DateTimeField()
    agent_taklif_bergan_vaqti = models.DateTimeField()
    latency_ms = models.IntegerField()
    feedback = models.CharField(
        max_length=16, choices=FEEDBACK_CHOICES, default=FEEDBACK_PENDING
    )
    feedback_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_takliflari"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["zapros"]),
            models.Index(fields=["mashina"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["feedback"]),
        ]

    def __str__(self):
        return f"Taklif #{self.pk}: zapros {self.zapros_id} -> mashina {self.mashina_id}"
