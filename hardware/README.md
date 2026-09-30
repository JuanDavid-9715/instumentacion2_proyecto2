# Hardware ESP32-S3

## Flasheo
1. Copia `secrets.py` real (no va a git) y `main.py` a la placa:
   `mpremote cp hardware/main.py :main.py && mpremote cp hardware/secrets.py :secrets.py`
2. Si es primera vez: `cp hardware/secrets.example.py hardware/secrets.py` y rellena WiFi/MQTT.
3. Reinicia y mira serial 115200.

## Topics
- `.../flujo/troncal|rama_a|rama_b` → JSON `{"s","q","ts"}` 1 Hz, QoS 0
- `.../control/bomba` ← `ON|OFF|TOGGLE`
- `.../estado/bomba` → `ON|OFF` retain

## Notas
- `secrets.py` jamás se commitea. `VENTANA=1000/PUB=1000`.
- K=7.5 datasheet ±10% (ver informe, sin calibrar).
- TLS `CERT_NONE` heredado (no tocar, ver M10).
