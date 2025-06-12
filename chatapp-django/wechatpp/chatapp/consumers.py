import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from chatapp.models import Room, Message
from channels.db import database_sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_slug']
        self.roomGroupName = 'chat_%s' % self.room_name
        
        await self.channel_layer.group_add(
            self.roomGroupName,
            self.channel_name
        )
        await self.accept()
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.roomGroupName,
            self.channel_name
        )
        
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
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
                }
            )
            # Broadcast to inbox group
            await self.channel_layer.group_send(
                "inbox", {
                    "type": "inbox_message",
                    "message": message,
                    "username": username,
                    "room_name": room_name,
                    "room_slug": self.room_name,
                    "created_on": message_obj.created_on.isoformat(),
                }
            )
        
    async def sendMessage(self, event):
        message = event["message"]
        username = event["username"]
        await self.send(text_data=json.dumps({
            "message": message,
            "username": username,
            "created_on": event["created_on"],
        }))
    
    @database_sync_to_async
    def save_message(self, message, username, room_name):
        try:
            user = User.objects.get(username=username)
            room = Room.objects.get(name=room_name)
            message_obj = Message.objects.create(user=user, room=room, content=message)
            return message_obj
        except User.DoesNotExist:
            print(f"User {username} not found")
            return None
        except Room.DoesNotExist:
            print(f"Room {room_name} not found")
            return None

class InboxConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("inbox", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("inbox", self.channel_name)

    async def inbox_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "username": event["username"],
            "room_name": event["room_name"],
            "room_slug": event["room_slug"],
            "created_on": event["created_on"],
        }))