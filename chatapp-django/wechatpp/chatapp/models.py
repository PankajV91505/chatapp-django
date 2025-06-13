from django.db import models
from django.contrib.auth.models import User

class Room(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('sent', 'Sent'),
            ('delivered', 'Delivered'),
            ('read', 'Read'),
        ],
        default='sent'
    )
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return f'Message by {self.user.username} in {self.room.name}'