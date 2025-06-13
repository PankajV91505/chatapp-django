from django.urls import path
from . import views, consumers

urlpatterns = [
    path('', views.redirect_to_chatbox, name='redirect_to_chatbox'),
    path('chatbox/', views.chatbox, name='chatbox'),
    path('api/messages/<slug:slug>/', consumers.get_messages, name='get_messages'),
    path('delete-messages/<slug:slug>/', views.delete_room_messages, name='delete_room_messages'),
]