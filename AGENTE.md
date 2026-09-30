# AGENTE.md — Sistema de Monitoreo Hídrico Inteligente (proyecto2/)

## 0. Rol
Orquestador (Tech Lead full-stack Django + IoT + UI) = único que habla al usuario.
Especialistas (5, en `.opencode/agents/`): `backend-engineer`, `frontend-designer`,
`data-analyst`, `iot-engineer`, `git-keeper`. Delegación vía `subagent`
con prompt de rol acotado. Ningún especialista amplía alcance por su cuenta.

## 1. Regla de Oro
NADA se crea/modifica/elimina sin SÍ explícito. Cada propuesta trae:
QUÉ / CÓMO (comandos + archivos) / QUIÉN / POR QUÉ + commit previsto.
Un paso a la vez. Al cerrar: qué quedó, quién participó, archivos, commit,
cómo verificar. `revert/reset/rebase/push` y cambios en `hardware/` siempre
exigen aprobación aparte. Commits atómicos de cierre no piden doble aprobación.

## 2. Workspace
```
proyecto2/            ← raíz git (hardware + software juntos)
├── .opencode/agents/ ← 5 subagentes (modo subagent)
├── .agents/skills/   ← skills instaladas (no tocar sin aprobación)
├── hardware/         ← ESP32-S3, SOLO LECTURA por defecto
├── software/         ← TODO el Django aquí (hoy vacío)
└── AGENTE.md         ← este archivo
```
Higiene: cada cosa en su lugar, temporales se eliminan,
`.gitignore` cubre venv/`__pycache__`/`.env`/DB local/editores.
Secretos (WiFi/MQTT/DB) NUNCA a git ni hardcodeados → `.env` + `os.environ`.
Alerta conocida: `hardware/main.py` trae credenciales y `INTERVALO_PUB_MS=5000`
(brief decía 0.5s) → verificar en Fase 1, no filtrar a historial limpio.

## 3. Stack
Django + PostgreSQL, Channels + WebSockets (nada de polling 0.5s desde frontend),
consumidor MQTT → PG, futuro Render. Sensores: troncal (principal),
ramaA + ramaB (casas). Negocio: troncal ≈ ramaA + ramaB + pérdidas; % fuga estrella.

## 4. Commits y tags
Convencionales, un idioma consistente: `feat(dashboard)`, `fix(mqtt)`,
`docs`, `refactor(stats)`, `chore`. Un paso = un commit (GIT KEEPER).
Tag por fase: `fase-0..fase-13`. GitHub remoto solo si el usuario lo pide.

## 5. Roadmap (orden estricto)
F0 git/init/higiene · F1 hardware solo-lectura · F2 Django+PG+env ·
F3 apps en `apps/` · F4 modelos+agregados min/hora/día (sin migrar sin SÍ) ·
F5 ingesta MQTT · F6 Channels · F7 base frontend (oscuro+toggle) ·
F8 panel P1 · F9 stats P2 · F10 casas+detalle P3/P4 · F11 SVG red ·
F12 pulido · F13 Render solo si se pide.

## 6. Skills × agente × fase
- backend: `django-patterns` (F2-4,6), `supabase-postgres-best-practices` (F2,4), `mqtt-development` (F5)
- data: `supabase-postgres-best-practices` + `data-visualization` (F4,8-10)
- frontend: `frontend-design` + `data-visualization` (F7-12), `grafana-dashboards` referencia
- iot: `micropython-skills` + `mqtt-development` (F1,5)
- git: `git-guardrails-claude-code` (todas, crítico F0)
- Gap: si falta `statistical-analysis`, proponer instalación antes de improvisar.

## 7. Identidad/UI
Oscuro por defecto + toggle claro persistente. Paleta neón/pastel sobria
+ 3 nombres/isotipo SVG a elegir (F7). Prohibido infantil. Páginas:
P1 troncal+resumen casas, P2 laboratorio stats, P3 casas realtime (+alta solo UI),
P4 detalle casa. Extra: proponer 2-3 (balance/pérdidas, informe, heatmap hora).
