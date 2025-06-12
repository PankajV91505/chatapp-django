from django.shortcuts import render
from .models import Room, Message
from django.db.models import Max

def rooms(request):
    rooms = Room.objects.all()
    return render(request, "rooms.html", {"rooms": rooms})

def room(request, slug):
    room_name = Room.objects.get(slug=slug).name
    messages = Message.objects.filter(room=Room.objects.get(slug=slug))
    return render(request, "room.html", {"room_name": room_name, "slug": slug, "messages": messages})

def inbox(request):
    if not request.user.is_authenticated:
        return render(request, "inbox.html", {"room_data": []})
    
    user_messages = Message.objects.filter(user=request.user).values('room').annotate(
        latest_message=Max('created_on')
    ).order_by('-latest_message')
    
    room_data = []
    for item in user_messages:
        room = Room.objects.get(id=item['room'])
        latest_message = Message.objects.filter(
            room=room, created_on=item['latest_message']
        ).first()
        if latest_message:
            room_data.append({
                "room": room,
                "latest_message": latest_message,
            })
    
    return render(request, "inbox.html", {"room_data": room_data})