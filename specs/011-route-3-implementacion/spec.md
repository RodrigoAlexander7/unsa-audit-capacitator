# Spec 011 — Ruta 3 completa: Implementación PIMS (24 h, Fase F10)

**Estado:** en ejecución (aprobado dentro del plan F8–F13).

## Objetivo
Completar los **9 módulos** de la Ruta 3 (`implementacion`, 1440 minutos = 24 horas), retirando `planned: true` de los módulos `01..03` y `05..09`, conservando intacto el módulo demo `04-declaracion-de-aplicabilidad`, y equipando cada módulo con lección práctica, ejemplo resuelto de la UNSA ficticia y ejercicio determinista donde el participante produce o completa los artefactos del PIMS.

## Criterios de aceptación (AC-011)
- **AC-011-1 (Estructura completa y 24 h):** La ruta `implementacion` tiene exactamente 9 módulos publicados (`planned: false`, `mandatory: true`), órdenes `1..9`, módulo 9 `is_final = True`, y suma exacta de `1440` minutos (`24 h`).
- **AC-011-2 (Preservación de R3 Módulo 04):** `04-declaracion-de-aplicabilidad` mantiene intacto su ejercicio `soa_form` sobre ORA (`AC-006-6`) y su sidecar de Biblioteca Central (`AC-009-10`).
- **AC-011-3 (Brecha, RAT e Incidentes — `document_form` en Módulos 01, 02 y 05):** `01-analisis-de-brecha` diagnostica el estado real de documentos UNSA; `02-inventario-de-activos-y-tratamientos` produce el RAT de `ORH` con regla `requires_if`; `05-politicas-y-procedimientos` parametriza el flujo de brechas e incidentes tomando `pims-programa-seguridad` como ejemplo resuelto.
- **AC-011-4 (Evaluación de riesgos operativa — `risk_table` en Módulo 03):** `03-evaluacion-de-riesgos` valora 5 activos UNSA completos con selección de vulnerabilidad y propietario del riesgo, aplicando consecuencia `2` en datos sensibles y umbral `< 3`.
- **AC-011-5 (Plan de tratamiento y residual — `treatment_table` en Módulo 06):** `06-plan-de-tratamiento-y-recursos` enlaza los riesgos no aceptables con controles **aplicables de la SoA** (rechazando controles no aplicables), asigna responsables/plazos y calcula riesgo residual coherente.
- **AC-011-6 (Registros, Indicadores faltantes y Examen final — Módulos 07, 08 y 09):** `07-evidencias-y-registros` usa `nonconformity_form` sobre registros y pruebas de respaldo; `08-indicadores` produce mediante `document_form` la ficha de monitoreo y revisión por dirección (`pims-monitoreo` faltante); `09-evaluacion-de-la-ruta` integra los 8 módulos previos mediante `quiz` de 10 preguntas (`final: true`).
- **AC-011-7 (Efectos colaterales en pruebas y seed):** `seed/solutions.py` resuelve al 100 % los 9 módulos de R3; `test_routes_2_4_content.py`, `test_routes_chain_api.py`, `test_analytics_api.py`, `test_demo_seed.py` y Playwright E2E verifican R3 completa (`24 h` en R3, `56 h` acumuladas R1–R4 antes de F11), manteniendo únicamente R4 con `planned` hasta F11.
- **AC-011-8 (Calidad, accesibilidad y restricciones):** Cumple `make verify` sin regresiones ni violaciones serias/críticas de `axe-core` y sin copiar contenido literal de `raw/`.
