from django.shortcuts import render, redirect
from .models import Room, Message
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@login_required
def rooms(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        if room_name:
            slug = slugify(room_name)
            room, created = Room.objects.get_or_create(name=room_name, slug=slug)
            if created:
                # Broadcast new room to inbox
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "inbox",
                    {
                        "type": "inbox_room",
                        "room_name": room_name,
                        "room_slug": slug,
                    }
                )
            return redirect('rooms')
    rooms = Room.objects.all()
    return render(request, "rooms.html", {"rooms": rooms})

@login_required
def room(request, slug):
    room_name = Room.objects.get(slug=slug).name
    messages = Message.objects.filter(room=Room.objects.get(slug=slug))
    return render(request, "room.html", {"room_name": room_name, "slug": slug, "messages": messages})

@login_required
def inbox(request):
    rooms = Room.objects.all()
    room_data = []
    for room in rooms:
        latest_message = Message.objects.filter(room=room).order_by('-created_on').first()
        room_data.append({
            "room": room,
            "latest_message": latest_message,
        })
    room_data.sort(key=lambda x: x['latest_message'].created_on if x['latest_message'] else x['room'].id, reverse=True)
    return render(request, "inbox.html", {"room_data": room_data})