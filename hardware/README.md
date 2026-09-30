# Nodo ESP32-S3 — Medición de flujo y control de bomba

## 1. Objetivo y alcance
Nodo de campo del Sistema de Monitoreo Hídrico (Instrumentación Industrial 2).
Mide caudal en 3 puntos de la red (troncal, ramaA, ramaB) con sensores YF-S2001,
publica por MQTT sobre TLS y permite control supervisado de la bomba.
No realiza agregación histórica ni balance oficial: eso es responsabilidad del backend (F4/F5).

## 2. Arquitectura y cadena de medida
Pulso Hall → interrupción por flanco ascendente → conteo en ventana fija →
frecuencia → caudal:

```
f [Hz] = Δpulsos × 1000 / ventana_real_ms
Q [L/min] = f / K,  con K = 7.5 Hz/(L/min) por datasheet
```

Balance indicativo solo a serial: `Δ = Q_troncal − (Q_ramaA + Q_ramaB)`.
El balance oficial y el % de pérdidas se calculan en el servidor.

## 3. Hardware y pinout
| GPIO | Función | Configuración | Nota |
|------|---------|---------------|------|
| 40 | Flujo troncal | IN pull-up + IRQ rising | YF-S2001 |
| 39 | Flujo rama A | IN pull-up + IRQ rising | YF-S2001 |
| 38 | Flujo rama B | IN pull-up + IRQ rising | YF-S2001 |
| 41 | Botón manual | IN pull-up, activo bajo | Toggle bomba, debounce 50 ms |
| 42 | Bomba (relé) | OUT, estado inicial OFF | Sin realimentación de campo |

Alimentación 5 V para sensores (señal 5 V tolerada por divisor o transistor según montaje),
ESP32-S3 a 3.3 V lógicos. Relé con aislamiento y diodo de libre circulación en bobina.

## 4. Tiempos y resolución
| Parámetro | Valor | Efecto |
|-----------|-------|--------|
| `VENTANA_MS` | 1000 | Ventana de conteo; se usa la ventana real medida por `ticks_diff` (M3), no la nominal |
| `POLL_MS` | 20 | Sondeo de botón + `check_msg` MQTT dentro de la ventana |
| `DEBOUNCE_MS` | 50 | Antirrebote del botón |
| `INTERVALO_PUB_MS` | 1000 | Publicación 1 Hz por sensor (3 msg/s totales) |

Resolución por cuantificación (1 pulso / ventana / K):
- 500 ms → ±0.267 L/min (descartada: peor resolución)
- 1000 ms → ±0.133 L/min (adoptada: equilibrio resolución / tiempo real)
- 2000 ms → ±0.067 L/min (solo si el proceso exige menor ruido a costa de 0.5 Hz)

A 0.5 s de publicación con ventana de 1 s se repetiría el mismo valor;
por eso PUB = VENTANA = 1000 ms (M1).

## 5. Protocolo MQTT
Broker HiveMQ Cloud, puerto 8883, TLS. Cliente fijo `esp32s3-001`
(el backend debe usar otro client_id para no colisionar).

| Tópico | Dirección | Payload | QoS/Retain | Tasa |
|--------|-----------|---------|------------|------|
| `InstrumentacionIndustrial/proyecto2/flujo/troncal` | nodo → servidor | `{"s":"troncal","q":4.267,"ts":1719792000}` | QoS 0, no retain | 1 Hz |
| `.../flujo/rama_a` | nodo → servidor | idem `s=rama_a` | QoS 0, no retain | 1 Hz |
| `.../flujo/rama_b` | nodo → servidor | idem `s=rama_b` | QoS 0, no retain | 1 Hz |
| `.../control/bomba` | servidor → nodo | `ON` / `OFF` / `TOGGLE` | QoS 0 | esporádico |
| `.../estado/bomba` | nodo → servidor | `ON` / `OFF` | QoS 0, **retain=True** | al cambio + arranque |

`q` en L/min con 3 decimales. `ts = time.time()` (NTP best-effort;
si falla, el servidor timestampea a ingesta y documenta el sesgo).
Criterio M6: flujo sin retain (dato de alta tasa), estado con retain
(último valor disponible al suscribirse).

## 6. Control de bomba y seguridad
- Arranque siempre en OFF (fail-safe). Ordenes válidas solo `ON/OFF/TOGGLE`;
  cualquier otro payload se ignora sin cambiar estado.
- Botón físico en GPIO 41 mantiene autoridad local (toggle).
- Cada cambio publica `estado` con retain para que el dashboard muestre
  el estado real sin sondeo.
- Sin enclavamientos de proceso en firmware: la lógica de permisos
  (zona empresa, acceso discreto) vive en el dashboard (F8).

## 7. Presupuesto de error (M4, sin calibrar)
K = 7.5 idéntico en las 3 ramas, valor de datasheet YF-S2001 con
tolerancia ±10% según presión, viscosidad, posición y tensión.
Consecuencia: `Δ = T − (A+B)` incluye sesgo de sensores además de
pérdidas reales. No se aplica calibración volumétrica en campo;
el informe declara esta tolerancia como causa de no-cierre.
Mejora futura: factores por rama obtenidos con volumen conocido
(1 L) sin cambiar la estructura del firmware.

## 8. Robustez (M2/M8)
- WiFi: verificación `isconnected()` cada ciclo + reconexión con reintentos;
  al arranque sin red, reinicio tras 5 s.
- MQTT: `check_msg()` no bloqueante cada 20 ms para atender `control/bomba`;
  ante fallo de publish, una reconexión y descarte del mensaje fallido
  (documentado: QoS 0 sin cola).
- Watchdog 30 s alimentado en ventana y tras publicar; recupera cuelgues
  en `connect/publish/sleep` sin intervención física.

## 9. Seguridad y límites conocidos (M9/M10)
- Credenciales fuera del código: `secrets.py` (real, no versionado) +
  `secrets.example.py` (plantilla versionada). `main.py` nunca contiene claves.
- TLS con `CERT_NONE` heredado del ejemplo provisto: cifra pero no valida
  el certificado. No se modifica (M10) para no romper la conectividad
  entregada; queda como limitación declarada.

## 10. Operación
1. `cp hardware/secrets.example.py hardware/secrets.py` y rellena WiFi/MQTT.
2. `mpremote cp hardware/main.py :main.py && mpremote cp hardware/secrets.py :secrets.py`
3. Reinicia, serial 115200.
4. Verificación: 1 línea/s `T/A/B/Δ/BOMBA` + 3 JSON/s publicados +
   `.../estado/bomba` retenido. Caída >12–15 s sin mensajes = nodo caído
   (sin LWT).
