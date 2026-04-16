import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat.

    URL: ws/chat/<conversation_id>/
    Inbound message format:  {"message": "hello"}
    Outbound message format: {"type": "chat_message", "message": "hello",
                               "sender_id": 1, "sender_name": "John Doe",
                               "timestamp": "2026-03-31T04:00:00Z"}
    """

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        # Reject unauthenticated or non-participant users
        if self.user.is_anonymous:
            await self.close()
            return

        is_participant = await self._is_participant()
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        """Handle incoming messages from WebSocket client."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        content = data.get('message', '').strip()
        if not content:
            return

        # Save to DB and get the serialised message back
        message_data = await self._save_message(content)

        # Broadcast to the conversation group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                **message_data,
            },
        )

    async def chat_message(self, event):
        """Handler for messages broadcast to the group."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
        }))

    # ── DB helpers ──────────────────────────────────────────────

    @database_sync_to_async
    def _is_participant(self):
        return Conversation.objects.filter(
            id=self.conversation_id,
            participants=self.user,
        ).exists()

    @database_sync_to_async
    def _save_message(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        msg = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
        )
        # Bump conversation updated_at
        conversation.save(update_fields=['updated_at'])

        return {
            'message': msg.content,
            'sender_id': self.user.id,
            'sender_name': self.user.get_full_name() or self.user.username,
            'timestamp': msg.created_at.isoformat(),
            'message_id': msg.id,
        }
