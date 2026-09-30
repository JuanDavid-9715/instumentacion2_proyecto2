import os

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import close_old_connections

from apps.dashboard.consumers import GRUPO
from apps.ingesta.mqtt import TOPICOS_FLUJO, TOPIC_ESTADO_BOMBA, crear_cliente, parsear_flujo
from apps.sensores.models import EstadoBomba, Sensor


def emitir(datos):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(GRUPO, {'type': 'flujo.update', 'datos': datos})


def manejar(topic, payload, log):
    close_old_connections()
    if topic in TOPICOS_FLUJO:
        codigo, q, ts = parsear_flujo(topic, payload)
        sensor, _ = Sensor.objects.get_or_create(
            codigo=codigo, defaults={'nombre': codigo, 'k_factor': 7.5})
        lec = sensor.lecturas.create(q=q, ts_nodo=ts)
        log(f'guardada {codigo} q={q:.3f}')
        emitir({codigo: {'q': q, 'ts': lec.ts_ingesta.isoformat()}})
    elif topic == TOPIC_ESTADO_BOMBA:
        estado = payload.decode().strip().upper() if isinstance(payload, bytes) else str(payload).strip().upper()
        if estado in ('ON', 'OFF'):
            EstadoBomba.objects.create(estado=estado, origen='mqtt')
            log(f'bomba {estado}')
            emitir({'bomba': estado})


def bucle(client_id, log=print):
    client, cred = crear_cliente(client_id)
    if not cred['host']:
        log('ingesta: falta MQTT_HOST en .env')
        return

    def on_connect(c, userdata, flags, rc):
        if rc != 0:
            log(f'ingesta: MQTT rc={rc}')
            return
        for t in list(TOPICOS_FLUJO) + [TOPIC_ESTADO_BOMBA]:
            c.subscribe(t, qos=0)
        log('ingesta: MQTT conectado y suscrito')

    def on_message(c, userdata, msg):
        try:
            manejar(msg.topic, msg.payload, log)
        except Exception as e:
            log(f'ingesta: descartado {msg.topic}: {e}')

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(cred['host'], cred['port'], keepalive=60)
    client.loop_forever()


def iniciar_en_hilo(client_id):
    import threading
    hilo = threading.Thread(target=bucle, args=(client_id,), daemon=True)
    hilo.start()
    return hilo


def nodos_para_credenciales():
    return list(TOPICOS_FLUJO) + [TOPIC_ESTADO_BOMBA]
