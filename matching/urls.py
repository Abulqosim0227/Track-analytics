from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("feedback/<int:taklif_id>/", views.submit_feedback, name="submit_feedback"),
]
