"""
Community Channels Consumers
============================
Handles WebSocket connections for Global Chat and Real-Time Notifications.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from apps.community.models import Notice
from apps.community.serializers import GlobalChatSerializer, NoticeSerializer
from channels.db import database_sync_to_async
from django.utils import timezone
import logging

logger = logging.getLogger("apps.community.consumers")

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return

        self.room_group_name = "global_chat"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
            
        try:
            text_data_json = json.loads(text_data)
            action = text_data_json.get("action", "chat")
            
            if action == "chat":
                message = text_data_json.get("text", "").strip()
                if not message:
                    return

                # Save message to DB
                saved_message = await self.save_message(self.user, message)
                
                if saved_message:
                    # Send message to room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "chat_message",
                            "message": saved_message
                        }
                    )
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"Error processing websocket message: {e}")

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "type": "chat",
            "data": message
        }))
        
    async def notification_message(self, event):
        notice = event["notice"]
        
        await self.send(text_data=json.dumps({
            "type": "notification",
            "data": notice
        }))

    @database_sync_to_async
    def save_message(self, user, text):
        from apps.community.services import add_chat_message
        try:
            msg = add_chat_message(user, text)
            return GlobalChatSerializer(msg).data
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return None
