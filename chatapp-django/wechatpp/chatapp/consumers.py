import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from chatapp.models import Room, Message
from channels.db import database_sync_to_async
from django.utils import timezone
from django.http import JsonResponse

# API to fetch messages for a room
def get_messages(request, slug):
    try:
        room = Room.objects.get(slug=slug)
        messages = Message.objects.filter(room=room).order_by('created_on')
        message_data = []
        for message in messages:
            try:
                read_by_usernames = list(message.read_by.values_list('username', flat=True))
            except Exception as e:
                print(f"Error accessing read_by for message {message.id}: {e}")
                read_by_usernames = []
            message_data.append({
                "user": message.user.username,
                "content": message.content,
                "created_on": message.created_on.isoformat(),
                "status": message.status,
                "read_by": read_by_usernames,
            })
        return JsonResponse(message_data, safe=False)
    except Room.DoesNotExist:
        return JsonResponse({"error": "Room not found"}, status=404)
    except Exception as e:
        print(f"Error in get_messages: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_slug']
        self.roomGroupName = 'room_%s' % self.room_name
        self.user = self.scope['user']
        
        await self.channel_layer.group_add(
            self.roomGroupName,
            self.channel_name
        )
        await self.accept()
        
        # Mark existing messages as read when user joins the room
        await self.mark_messages_as_read()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.roomGroupName,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "message")

        if message_type == "message":
            message = text_data_json["message"]
            username = text_data_json["username"]
            room_name = text_data_json["room_name"]
            
            message_obj = await self.save_message(message, username, room_name)
            if message_obj:
                # Broadcast to room group
                await self.channel_layer.group_send(
                    self.roomGroupName, {
                        "type": "sendMessage",
                        "message": message,
                        "username": username,
                        "room_name": room_name,
                        "created_on": message_obj.created_on.isoformat(),
                        "status": message_obj.status,
                    }
                )
                # Broadcast to chatbox group (for room list updates)
                await self.channel_layer.group_send(
                    "chatbox", {
                        "type": "chatbox_message",
                        "message": message,
                        "username": username,
                        "room_name": room_name,
                        "room_slug": self.room_name,
                        "created_on": message_obj.created_on.isoformat(),
                    }
                )
        elif message_type == "typing":
            username = text_data_json["username"]
            await self.channel_layer.group_send(
                self.roomGroupName, {
                    "type": "typingMessage",
                    "username": username,
                }
            )

    async def sendMessage(self, event):
        message = event["message"]
        username = event["username"]
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": message,
            "username": username,
            "created_on": event["created_on"],
            "status": event["status"],
        }))

    async def typingMessage(self, event):
        username = event["username"]
        await self.send(text_data=json.dumps({
            "type": "typing",
            "username": username,
        }))

    @database_sync_to_async
    def save_message(self, message, username, room_name):
        try:
            user = User.objects.get(username=username)
            room = Room.objects.get(name=room_name)
            message_obj = Message.objects.create(
                user=user,
                room=room,
                content=message,
                status='delivered'
            )
            return message_obj
        except User.DoesNotExist:
            print(f"User {username} not found")
            return None
        except Room.DoesNotExist:
            print(f"Room {room_name} not found")
            return None

    @database_sync_to_async
    def mark_messages_as_read(self):
        try:
            room = Room.objects.get(slug=self.room_name)
            messages = Message.objects.filter(room=room).exclude(user=self.user)
            for message in messages:
                if self.user not in message.read_by.all():
                    message.read_by.add(self.user)
                    message.status = 'read'
                    message.save()
        except Room.DoesNotExist:
            print(f"Room {self.room_name} not found")

class ChatboxConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("chatbox", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("chatbox", self.channel_name)

    async def chatbox_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "username": event["username"],
            "room_name": event["room_name"],
            "room_slug": event["room_slug"],
            "created_on": event["created_on"],
        }))

    async def chatbox_room(self, event):
        await self.send(text_data=json.dumps({
            "type": "chatbox_room",
            "room_name": event["room_name"],
            "room_slug": event["room_slug"],
        }))