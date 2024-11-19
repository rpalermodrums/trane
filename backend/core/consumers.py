import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ProcessingProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'task_{self.task_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def progress_update(self, event):
        # Send progress update to WebSocket
        await self.send(text_data=json.dumps({
            'progress': event['progress'],
            'status': event['status']
        })) 