import machine
import network
import ssl
import time
import json
import secrets as creds

PIN_TRONCAL = 40
PIN_RAMA_A = 39
PIN_RAMA_B = 38
PIN_BOTON = 41
PIN_BOMBA = 42

VENTANA_MS = 1000
POLL_MS = 20
DEBOUNCE_MS = 50
INTERVALO_PUB_MS = 1000
WDT_TIMEOUT_MS = 30000

K_TRONCAL = 7.5
K_RAMA_A = 7.5
K_RAMA_B = 7.5

BASE = "InstrumentacionIndustrial/proyecto2"
TOPIC_TRONCAL = (BASE + "/flujo/troncal").encode()
TOPIC_RAMA_A = (BASE + "/flujo/rama_a").encode()
TOPIC_RAMA_B = (BASE + "/flujo/rama_b").encode()
TOPIC_CONTROL_BOMBA = (BASE + "/control/bomba").encode()
TOPIC_ESTADO_BOMBA = (BASE + "/estado/bomba").encode()


class Bomba:
    def __init__(self, pin):
        self._pin = machine.Pin(pin, machine.Pin.OUT)
        self.apagar()

    def encender(self):
        self._pin.on()

    def apagar(self):
        self._pin.off()

    def toggle(self):
        self.apagar() if self.encendida() else self.encender()

    def encendida(self):
        return self._pin.value() == 1

    def estado(self):
        return "ON" if self.encendida() else "OFF"


class Boton:
    def __init__(self, pin, on_press):
        self._pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self._on_press = on_press
        self._prev = 1
        self._flanco = 0

    def actualizar(self):
        actual = self._pin.value()
        if actual != self._prev:
            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, self._flanco) >= DEBOUNCE_MS:
                self._prev = actual
                self._flanco = ahora
                if actual == 0:
                    self._on_press()


class SensorFlujo:
    def __init__(self, pin, codigo, k_factor, topic):
        self.codigo = codigo
        self.k_factor = k_factor
        self.topic = topic
        self.caudal = 0.0
        self.pulsos = 0
        self._p0 = 0
        self._pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self._pin.irq(trigger=machine.Pin.IRQ_RISING, handler=self._isr)

    def _isr(self, pin):
        self.pulsos += 1

    def iniciar_ventana(self):
        self._p0 = self.pulsos

    def cerrar_ventana(self, ventana_real_ms):
        delta = self.pulsos - self._p0
        self.caudal = (delta * 1000.0 / ventana_real_ms) / self.k_factor


class Wifi:
    def __init__(self):
        self._w = network.WLAN(network.STA_IF)
        self._w.active(True)

    def conectado(self):
        return self._w.isconnected()

    def conectar(self, reintentos=20, espera_s=0.5):
        if self.conectado():
            return True
        self._w.connect(creds.WIFI_SSID, creds.WIFI_PASS)
        for _ in range(reintentos):
            if self.conectado():
                print("WiFi OK:", self._w.ifconfig()[0])
                return True
            time.sleep(espera_s)
        return False


class Mqtt:
    def __init__(self, bomba):
        self._bomba = bomba
        self._client = None

    def _al_recibir(self, topic, mensaje):
        orden = mensaje.decode().strip().upper()
        if topic == TOPIC_CONTROL_BOMBA:
            if orden == "ON":
                self._bomba.encender()
            elif orden == "OFF":
                self._bomba.apagar()
            elif orden == "TOGGLE":
                self._bomba.toggle()
            self.publicar(TOPIC_ESTADO_BOMBA, self._bomba.estado(), retain=True)

    def conectar(self):
        from umqtt.simple import MQTTClient
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.verify_mode = ssl.CERT_NONE
        self._client = MQTTClient(
            creds.MQTT_ID, creds.MQTT_HOST,
            port=creds.MQTT_PORT,
            user=creds.MQTT_USER, password=creds.MQTT_PASS,
            keepalive=60, ssl=ctx,
        )
        self._client.set_callback(self._al_recibir)
        self._client.connect()
        self._client.subscribe(TOPIC_CONTROL_BOMBA)
        print("MQTT conectado")

    def revisar(self):
        try:
            self._client.check_msg()
        except Exception as e:
            print("MQTT check:", e)
            self.conectar()

    def publicar(self, topic, mensaje, retain=False):
        try:
            self._client.publish(topic.encode() if isinstance(topic, str) else topic,
                                 mensaje.encode(), retain=retain, qos=0)
            return True
        except Exception as e:
            print("Error MQTT:", e)
            try:
                self.conectar()
            except Exception as e2:
                print("Reconexion MQTT:", e2)
            return False


def sincronizar_hora():
    try:
        import ntptime
        ntptime.settime()
        print("NTP OK:", time.time())
    except Exception as e:
        print("NTP omitido:", e)


def main():
    troncal = SensorFlujo(PIN_TRONCAL, "troncal", K_TRONCAL, TOPIC_TRONCAL)
    rama_a = SensorFlujo(PIN_RAMA_A, "rama_a", K_RAMA_A, TOPIC_RAMA_A)
    rama_b = SensorFlujo(PIN_RAMA_B, "rama_b", K_RAMA_B, TOPIC_RAMA_B)
    sensores = [troncal, rama_a, rama_b]

    bomba = Bomba(PIN_BOMBA)
    boton = Boton(PIN_BOTON, on_press=bomba.toggle)
    wifi = Wifi()
    mqtt = Mqtt(bomba)
    wdt = machine.WDT(timeout=WDT_TIMEOUT_MS)

    print("=== Sensores + bomba + MQTT - ESP32-S3 ===")

    if not wifi.conectar():
        print("Sin WiFi. Reiniciando en 5s...")
        time.sleep(5)
        machine.reset()

    sincronizar_hora()

    try:
        mqtt.conectar()
    except Exception as e:
        print("Error MQTT:", e)
        time.sleep(5)
        machine.reset()

    mqtt.publicar(TOPIC_ESTADO_BOMBA, bomba.estado(), retain=True)
    ultimo_estado = bomba.estado()
    t_ultima_pub = time.ticks_ms() - INTERVALO_PUB_MS

    try:
        while True:
            if not wifi.conectado():
                print("WiFi caido. Reconectando...")
                wifi.conectar()
            for s in sensores:
                s.iniciar_ventana()

            t0 = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), t0) < VENTANA_MS:
                boton.actualizar()
                mqtt.revisar()
                wdt.feed()
                time.sleep_ms(POLL_MS)
            ventana_real = time.ticks_diff(time.ticks_ms(), t0)

            for s in sensores:
                s.cerrar_ventana(ventana_real)

            print("{:.3f} T={:.3f} A={:.3f} B={:.3f} D={:+.3f} BOMBA={}".format(
                time.time(),
                troncal.caudal, rama_a.caudal, rama_b.caudal,
                troncal.caudal - rama_a.caudal - rama_b.caudal,
                bomba.estado()))

            if bomba.estado() != ultimo_estado:
                mqtt.publicar(TOPIC_ESTADO_BOMBA, bomba.estado(), retain=True)
                ultimo_estado = bomba.estado()

            if time.ticks_diff(time.ticks_ms(), t_ultima_pub) >= INTERVALO_PUB_MS:
                for s in sensores:
                    mqtt.publicar(s.topic, json.dumps(
                        {"s": s.codigo, "q": round(s.caudal, 3), "ts": time.time()}))
                t_ultima_pub = time.ticks_ms()
            wdt.feed()

    except KeyboardInterrupt:
        bomba.apagar()
        print("\nDetenido.")


if __name__ == "__main__":
    main()
