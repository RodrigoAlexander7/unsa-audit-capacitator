# Spec 010 — Ruta 2 completa: Interpretación PIMS (16 h, Fase F9)

**Estado:** en ejecución (aprobado dentro del plan F8–F13).

## Objetivo
Desarrollar e integrar los **8 módulos completos** de la Ruta 2 (`interpretacion`, 960 minutos = 16 horas) eliminando todos los estados `planned`, dotando a cada módulo de:
1. Lección práctica adaptada a la UNSA ficticia e ISO/IEC 27701 sobre 27001 (sin reproducir texto literal ni identificadores del Anexo A ni plantillas de terceros).
2. Ejemplo resuelto institucional (`reference_doc` vigente o sidecar `*.reference.md` coherente).
3. Ejercicio interactivo con criterio real de implementador/auditor y corrección determinista en backend (`document_form`, `risk_table`, `soa_form`, `branching`, `matching`, `competence_matrix`, `quiz`).
4. Módulo 8 marcado `final: true` y bloqueado hasta aprobar `01..07`.

## Criterios de aceptación (AC-010)
- **AC-010-1 (Completitud y carga horaria de R2):** La ruta `interpretacion` contiene exactamente 8 módulos publicados (`planned: false`, `mandatory: true`), con órdenes consecutivos `1..8`, módulo 8 marcado `is_final = True`, y suma exacta de `960` minutos (`16` horas).
- **AC-010-2 (Integridad del módulo 06 previo):** El módulo `06-del-requisito-al-documento` conserva su `matching` sobre los 11 requisitos reales de `content/pims/requirements.yaml` (`AC-006-4`), añadiendo únicamente soporte visual de referencia lado a lado.
- **AC-010-3 (Práctica documental real en Módulos 01 y 02 — `document_form`):** Los módulos `01-contexto-y-alcance` y `02-liderazgo-y-politica` emplean `document_form` con `reference_doc` vigente (`pims-alcance`, `pims-politica-privacidad`), validación de fechas (`date_order`), segregación de roles (`disjoint`), coherencia unidad↔sistema y rúbricas estructurales con rechazo a anti-patrones.
- **AC-010-4 (Evaluación de riesgos con datos sensibles en Módulo 03 — `risk_table`):** El módulo `03-riesgos-de-privacidad` valida mediante `risk_table` la escala UNSA (`C + P`), el umbral `< 3` y la exigencia de consecuencia alta (`2`) cuando intervienen datos sensibles, acompañado de ejemplo resuelto sin contradecir el vencimiento simulado de BD.
- **AC-010-5 (Aplicabilidad y roles controller/processor en Módulos 04 y 05):** El módulo `04-controles-y-aplicabilidad` practica decisiones `soa_form` rechazando exclusiones por costo/comodidad; el módulo `05-controller-y-processor` practica escenarios `branching` reales sobre infraestructura `OTI`, proveedor nube y laboratorio médico externo (`OBU`/`FCSA`).
- **AC-010-6 (Competencia eficaz y evaluación final en Módulos 07 y 08):** El módulo `07-competencia-monitoreo-mejora` usa `competence_matrix` contra `pims-competencia` exigiendo evidencia de eficacia real y evaluador imparcial; el módulo `08-evaluacion-de-la-ruta` integra los 7 temas mediante `quiz` de 10 preguntas (`final: true`), acreditando las `16` horas al aprobar.
- **AC-010-7 (Efectos colaterales: seed demo, analytics y cadena de rutas):** `seed/solutions.py` resuelve al 100 % los 8 módulos de R2, el cohorte demo y las pruebas de integración (`test_routes_2_4_content.py`, `test_routes_chain_api.py`, `test_analytics_api.py`, `test_demo_seed.py`) reflejan `16 h` en R2 y `35 h` acumuladas al completar R1–R4 actuales, manteniendo R3 y R4 con su estructura previa hasta F10/F11.
- **AC-010-8 (Calidad, accesibilidad y restricciones):** Cumple `make verify` completo (ruff, pyright, prettier, svelte-check, pytest, vitest, playwright + axe-core sin violaciones serias/críticas, alembic check y build) y 0 copias literales desde `raw/`.
