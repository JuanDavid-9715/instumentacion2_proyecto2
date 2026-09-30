from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand
from django.db import close_old_connections

from apps.dashboard.consumers import GRUPO
from apps.ingesta.mqtt import TOPICOS_FLUJO, TOPIC_ESTADO_BOMBA, crear_cliente, parsear_flujo
from apps.sensores.models import EstadoBomba, Sensor


def emitir(datos):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(GRUPO, {'type': 'flujo.update', 'datos': datos})


class Command(BaseCommand):
    help = 'Suscribe flujo 1Hz + estado bomba y guarda en BD'

    def handle(self, *args, **options):
        client, cred = crear_cliente('dashboard-001')
        if not cred['host']:
            self.stderr.write('Falta MQTT_HOST en .env')
            return

        def on_connect(c, userdata, flags, rc):
            if rc != 0:
                self.stderr.write(f'MQTT rc={rc}')
                return
            for t in list(TOPICOS_FLUJO) + [TOPIC_ESTADO_BOMBA]:
                c.subscribe(t, qos=0)
            self.stdout.write('MQTT conectado y suscrito')

        def on_message(c, userdata, msg):
            close_old_connections()
            topic = msg.topic
            if topic in TOPICOS_FLUJO:
                try:
                    codigo, q, ts = parsear_flujo(topic, msg.payload)
                    sensor = Sensor.objects.get(codigo=codigo)
                    lec = sensor.lecturas.create(q=q, ts_nodo=ts)
                    emitir({codigo: {'q': q, 'ts': lec.ts_ingesta.isoformat()}})
                except Exception as e:
                    self.stderr.write(f'descartado {topic}: {e}')
            elif topic == TOPIC_ESTADO_BOMBA:
                estado = msg.payload.decode().strip().upper()
                if estado in ('ON', 'OFF'):
                    EstadoBomba.objects.create(estado=estado, origen='mqtt')
                    emitir({'bomba': estado})

        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(cred['host'], cred['port'], keepalive=60)
        client.loop_forever()
