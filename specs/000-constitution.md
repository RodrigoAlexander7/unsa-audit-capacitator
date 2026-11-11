# Constitution — Plataforma Capacitadora UNSA (POC)

Principios no negociables. Cualquier spec, plan o PR que los contradiga debe modificar primero este documento (con ADR).

## 1. Spec primero
- Ninguna feature se implementa sin `specs/NNN-*/spec.md` aprobada (historias + criterios de aceptación `AC-NNN-x` en Given/When/Then).
- Todo test referencia el AC que verifica. Si la realidad cambia, se actualiza la spec en el mismo cambio.
- El contrato de API (`contracts/openapi.yaml`) se escribe antes de implementar.

## 2. Clean Architecture
- Dependencias hacia adentro: `domain ← application ← infrastructure / interface`.
- `domain` y `application` no importan FastAPI, SQLAlchemy, subprocess ni librerías de I/O.
- Puertos en `application`; adaptadores en `infrastructure`. Composición solo en `main.py`.
- La API es la fuente de verdad de reglas críticas (gating, horas, notas). El frontend no las recalcula.

## 3. Datos ficticios y privacidad
- Todo dato de la UNSA es **ficticio** y se marca como tal en UI y en cada plantilla.
- Nunca se envían nombres, emails ni datos personales a la IA: solo agregados anonimizados.
- Sin secretos en el repo. Configuración por `.env` (ignorado) y `.env.example`.

## 4. Seguridad por defecto
- Subprocess (`agy`) siempre sin shell, con timeout, límite de salida y sandbox.
- Contraseñas con Argon2; JWT con expiración; endpoints admin verifican rol en backend.

## 5. Producto
- Enfoque práctico: ejercicios interactivos sobre teoría.
- Un único tema claro en el frontend. Español como idioma de UI y contenido.
- Contenido ISO parafraseado; nunca se reproduce texto de la norma.

## 6. Calidad mínima
- `ruff`, `pyright/mypy`, `pytest`, `svelte-check`, `eslint`, `vitest` pasan antes de dar una fase por cerrada.
- Cada fase termina con su "entregable verificable" demostrado.
- Specs cortas (1–2 páginas): una por fase, no por función.
