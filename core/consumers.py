import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TeamPingConsumer(AsyncWebsocketConsumer):
    async def keen_connect(self):
        self.group_name = "team_ping"
        
        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
    async def connect(self):
        # We need to ensure the user is authenticated
        if self.scope["user"].is_anonymous:
            await self.close()
        else:
            await self.keen_connect()

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Receive message from room group
    async def team_ping_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event["data"]))
