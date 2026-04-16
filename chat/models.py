from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """
    A conversation between two (or more, for future group chat) users.
    Uses ManyToMany participants so extending to group chats requires
    no schema migration — just UI and consumer logic changes.
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        names = ', '.join(
            u.get_full_name() or u.username
            for u in self.participants.all()[:4]
        )
        return f'Conversation({self.id}): {names}'


class Message(models.Model):
    """A single chat message within a conversation."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Message({self.id}) by {self.sender} at {self.created_at:%H:%M}'
