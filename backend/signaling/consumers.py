import json
from channels.generic.websocket import AsyncWebsocketConsumer

# In-memory room registry: room_name -> {channel_name: True}
# Single Render worker means this is safe; upgrade to Redis channel layer for multi-worker.
_rooms: dict[str, dict[str, bool]] = {}


class SignalingConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = 'sig_' + self.room_name

        # Register before joining so existing peers know who just arrived
        if self.room_name not in _rooms:
            _rooms[self.room_name] = {}

        existing_peers = list(_rooms[self.room_name].keys())

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Tell the newcomer: (a) their own peer ID, (b) who's already here
        await self.send(text_data=json.dumps({
            'type': 'init',
            'peerId': self.channel_name,
            'peers': existing_peers,
        }))

        # Tell everyone already in the room that a new peer arrived
        await self.channel_layer.group_send(self.group_name, {
            'type': 'evt_peer_joined',
            'peerId': self.channel_name,
            'from_channel': self.channel_name,
        })

        _rooms[self.room_name][self.channel_name] = True

    async def disconnect(self, close_code):
        if self.room_name in _rooms:
            _rooms[self.room_name].pop(self.channel_name, None)
            if not _rooms[self.room_name]:
                del _rooms[self.room_name]

        # Tell remaining peers this one left
        await self.channel_layer.group_send(self.group_name, {
            'type': 'evt_peer_left',
            'peerId': self.channel_name,
            'from_channel': self.channel_name,
        })

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        data['from_channel'] = self.channel_name

        target = data.get('to')
        if target:
            # Point-to-point: offer / answer / ICE — send only to the intended peer
            await self.channel_layer.send(target, {
                'type': 'direct_message',
                'message': data,
            })
        else:
            # Broadcast: chat, or any message with no target
            await self.channel_layer.group_send(self.group_name, {
                'type': 'broadcast_message',
                'message': data,
            })

    # ── Channel-layer event handlers ──────────────────────────────────────────

    async def broadcast_message(self, event):
        msg = event['message']
        if msg.get('from_channel') != self.channel_name:
            await self.send(text_data=json.dumps(msg))

    async def direct_message(self, event):
        # Always deliver — already targeted at this channel
        await self.send(text_data=json.dumps(event['message']))

    async def evt_peer_joined(self, event):
        if event['from_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'peer_joined',
                'peerId': event['peerId'],
            }))

    async def evt_peer_left(self, event):
        if event['from_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'peer_left',
                'peerId': event['peerId'],
            }))
