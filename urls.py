from django.urls import path

from . import views

app_name = "greetings"

urlpatterns = [
    path("", views.index, name="index"),
]
