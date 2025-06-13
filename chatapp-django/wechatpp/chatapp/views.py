from django.shortcuts import render, redirect
from .models import Room, Message
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime
from django.utils import timezone
from django.http import JsonResponse

@login_required
def chatbox(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        if room_name:
            slug = slugify(room_name)
            room, created = Room.objects.get_or_create(name=room_name, slug=slug)
            if created:
                # Broadcast new room to all clients
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "chatbox",
                    {
                        "type": "chatbox_room",
                        "room_name": room_name,
                        "room_slug": slug,
                    }
                )
    rooms = Room.objects.all()
    room_data = []
    for room in rooms:
        latest_message = Message.objects.filter(room=room).order_by('-created_on').first()
        room_data.append({
            "room": room,
            "latest_message": latest_message,
        })
    # Use a timezone-aware datetime as fallback
    room_data.sort(
        key=lambda x: x['latest_message'].created_on if x['latest_message'] else timezone.make_aware(datetime.min),
        reverse=True
    )
    return render(request, "chatbox.html", {"room_data": room_data})

@login_required
def delete_room_messages(request, slug):
    if request.method == 'POST':
        try:
            room = Room.objects.get(slug=slug)
            Message.objects.filter(room=room).delete()
            return JsonResponse({"status": "success", "message": "Messages deleted successfully"})
        except Room.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Room not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

def redirect_to_chatbox(request):
    return redirect('chatbox')