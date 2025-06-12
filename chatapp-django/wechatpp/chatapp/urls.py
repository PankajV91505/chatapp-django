from django.urls import path
from . import views

urlpatterns = [
    path("", views.rooms, name="rooms"),
    path("inbox/", views.inbox, name="inbox"),
    path("<str:slug>", views.room, name="room"),
]