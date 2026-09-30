import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

GRUPO = 'flujos'


@database_sync_to_async
def ultima_lectura():
    from apps.sensores.models import Lectura
    datos = {}
    for codigo in ('troncal', 'rama_a', 'rama_b'):
        lec = Lectura.objects.filter(sensor__codigo=codigo).order_by('-ts_ingesta').first()
        if lec:
            datos[codigo] = {'q': lec.q, 'ts': lec.ts_ingesta.isoformat()}
    return datos


class FlujoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(GRUPO, self.channel_name)
        await self.accept()
        await self.send_json({'tipo': 'snapshot', 'datos': await ultima_lectura()})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(GRUPO, self.channel_name)

    async def receive_json(self, content, **kwargs):
        pass

    async def flujo_update(self, event):
        await self.send_json({'tipo': 'flujo', 'datos': event['datos']})
