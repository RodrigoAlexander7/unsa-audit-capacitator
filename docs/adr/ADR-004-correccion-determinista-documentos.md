# ADR-004 — Corrección determinista y sin IA de la práctica documental

- **Estado:** aceptada (Fase F8, Spec 009)
- **Fecha:** 2026-11-11

## Contexto
Las rutas 2–4 exigen que el participante diligencie documentos y matrices reales de un PIMS ISO/IEC 27701 sobre 27001 (`Alcance`, `Matriz de evaluación de riesgos`, `Plan de tratamiento`, `Lista de apoyo de auditoría interna`, `Formulario de no conformidad y acción correctiva`, `Matriz de competencia y capacitación`) inspirados estructuralmente en las 16 plantillas inventariadas en [inventario-plantillas.md](file:///home/totora/Documents/PROFESIONAL/unsa-audit-capacitator/docs/practica-documental/inventario-plantillas.md).

Evaluar estos documentos con un LLM introduciría no determinismo, latencia, dependencia externa en cada intento y riesgo de filtrar criterios incoherentes frente a las reglas normativas del dominio.

## Decisión
- **Motor puro y determinista en `learning/domain` (`document_exercises.py`):** se añaden 6 `ExerciseKind` (`document_form`, `risk_table`, `treatment_table`, `audit_checklist`, `nonconformity_form`, `competence_matrix`) con funciones puras de validación (`validate_spec`), saneamiento (`to_public`), calificación (`grade`) y guía (`solution_guide`). Ninguna corrección invoca IA ni red.
- **Evaluación estructural de texto libre:** los campos abiertos (`textarea`) se califican por rúbricas estructurales normalizadas (longitud mínima útil, grupos de palabras clave obligatorias y anti-patrones prohibidos).
- **Reglas entre campos y trazabilidad:**
  - `document_form` valida reglas cruzadas (`date_order`, `disjoint`, `requires_if`, `unit_system_coherence`, `count_matches`).
  - `risk_table` calcula `C + P` en backend, compara con `threshold` y exige consecuencia alta (`2`) ante categorías sensibles.
  - `treatment_table` impide incrementar el riesgo residual o elegir controles marcados como no aplicables en la SoA.
  - `nonconformity_form` separa contención inmediata de acción correctiva, valida coherencia entre fechas con `min_verification_lag_days` y cambio documental.
  - `audit_checklist_from_pims` genera ítems reales desde `pims_requirements` y el estado vigente en BD (`missing`, `draft`, `expired`, `unowned`, `in_force`).
- **Política de intentos agotados:** `to_public` nunca incluye respuestas esperadas ni rúbricas privadas; tras `REVEAL_AFTER_ATTEMPTS = 3` intentos fallidos (`not passed`), `AttemptResponse` devuelve `solution_revealed = True` y `solution_guide` por cada ítem o regla pendiente, manteniendo `passed = False` hasta que el participante corrija y reenvíe.
- **Vista lado a lado:** `Module` incorpora `reference_title` y `reference_md` resueltos desde `reference_doc` (p. ej. `content/institutional/pims-*`) o desde un sidecar `*.reference.md` sin colisionar con la carga de módulos ni las reglas legales sobre plantillas de terceros.

## Consecuencias
+ Cada intento es 100 % reproducible, auditable, instantáneo y comprobable con tests unitarios de dominio y de integración.
+ El asistente pedagógico flotante (F12–F13) podrá ayudar a comprender conceptos sin convertirse en calificador.
− Los escenarios con texto abierto requieren redactar rúbricas cuidadosas (sinónimos y anti-patrones) para evitar falsos negativos.
