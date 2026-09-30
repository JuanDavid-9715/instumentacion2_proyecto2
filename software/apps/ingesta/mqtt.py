import json
import os

import paho.mqtt.client as mqtt

BASE = 'InstrumentacionIndustrial/proyecto2'
TOPIC_TRONCAL = f'{BASE}/flujo/troncal'
TOPIC_RAMA_A = f'{BASE}/flujo/rama_a'
TOPIC_RAMA_B = f'{BASE}/flujo/rama_b'
TOPIC_CONTROL_BOMBA = f'{BASE}/control/bomba'
TOPIC_ESTADO_BOMBA = f'{BASE}/estado/bomba'

TOPICOS_FLUJO = {
    TOPIC_TRONCAL: 'troncal',
    TOPIC_RAMA_A: 'rama_a',
    TOPIC_RAMA_B: 'rama_b',
}

ORDENES_VALIDAS = ('ON', 'OFF', 'TOGGLE')


def parsear_flujo(topic, payload):
    try:
        codigo = TOPICOS_FLUJO[topic]
    except KeyError:
        raise ValueError(f'topic desconocido: {topic}')
    texto = payload.decode().strip() if isinstance(payload, bytes) else str(payload).strip()
    try:
        datos = json.loads(texto)
        return codigo, float(datos['q']), datos.get('ts')
    except (ValueError, KeyError, TypeError):
        return codigo, float(texto), None


def _credenciales():
    return {
        'host': os.environ.get('MQTT_HOST', ''),
        'port': int(os.environ.get('MQTT_PORT', '8883')),
        'user': os.environ.get('MQTT_USER', ''),
        'password': os.environ.get('MQTT_PASS', ''),
    }


def crear_cliente(client_id):
    c = _credenciales()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
    if c['user']:
        client.username_pw_set(c['user'], c['password'])
    client.tls_set()
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    return client, c


def publicar_orden_bomba(orden):
    orden = orden.strip().upper()
    if orden not in ORDENES_VALIDAS:
        raise ValueError(f'orden inválida: {orden}')
    client, c = crear_cliente('dashboard-pub-001')
    client.connect(c['host'], c['port'], keepalive=60)
    client.loop_start()
    info = client.publish(TOPIC_CONTROL_BOMBA, orden, qos=0)
    info.wait_for_publish(timeout=10)
    client.loop_stop()
    client.disconnect()
    return True
