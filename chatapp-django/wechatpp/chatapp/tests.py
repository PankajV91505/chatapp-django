from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from chatapp.models import Room, Message

class ChatappTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.room = Room.objects.create(name='Test Room', slug='test-room')
        self.client.login(username='testuser', password='testpass')

    def test_inbox_view_authenticated(self):
        response = self.client.get(reverse('inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inbox.html')

    def test_inbox_view_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inbox.html')
        self.assertEqual(len(response.context['room_data']), 0)

    def test_inbox_with_messages(self):
        Message.objects.create(
            user=self.user,
            content='Hello, world!',
            room=self.room
        )
        response = self.client.get(reverse('inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['room_data']), 1)
        self.assertEqual(response.context['room_data'][0]['room'].name, 'Test Room')

    def test_rooms_view(self):
        response = self.client.get(reverse('rooms'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rooms.html')

    def test_room_view(self):
        response = self.client.get(reverse('room', args=['test-room']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'room.html')