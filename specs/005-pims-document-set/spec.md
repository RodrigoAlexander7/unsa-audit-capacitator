# Spec 005 — Conjunto documental del PIMS (ISO/IEC 27701)

**Estado:** aprobada (plan v2, Fase 4)

## Objetivo
Dar a la UNSA ficticia el **conjunto de información documentada de su PIMS** (11 requisitos) como documentos versionados, con una **matriz de trazabilidad** requisito ↔ documento ↔ responsable ↔ estado y un panel de **completitud**. Es el eje común de las Rutas 2, 3 y 4 y el material auditable de la Ruta 4. El contenido se redacta de nuevo (no se copian plantillas de terceros; ver `docs/adaptacion-plantillas-27001-a-27701.md`).

## Historias
- **H1.** Como participante quiero ver qué documentos exige el PIMS, qué cláusula los motiva y qué evidencia se espera.
- **H2.** Como participante quiero saber cuáles documentos existen y en qué estado están (vigente, borrador, vencido, sin responsable, inexistente).
- **H3.** Como futuro auditor quiero un conjunto realista con carencias para practicar la detección de hallazgos.
- **H4.** Como equipo quiero guardar las cláusulas como **datos** para poder corregir la numeración según la edición de la norma.

## Reglas de negocio
1. Los 11 requisitos (orden del PLAN §5): alcance (4.3), política de privacidad (5.2), proceso de evaluación de riesgos de privacidad (6.1.2), declaración de aplicabilidad (6.1.3 e), plan de tratamiento (6.1.3 f), programa de seguridad documentado con gestión de incidentes (6.1.3 c), resultados de la evaluación de riesgos (8.2), resultados del tratamiento (8.3), evidencia de competencia (7.2), evidencia de monitoreo y medición (9.1), evidencia de no conformidades y acciones correctivas (10.2).
2. Cada requisito se cumple con **un documento de un tipo propio** (`PIMS_*`); los documentos PIMS son documentos normales (versiones, diff, solicitudes de cambio).
3. Un documento tiene **ciclo de vida** (`in_force` | `draft`) y **fecha de revisión** opcional. Los documentos preexistentes (F3) quedan `in_force` sin fecha.
4. Estado de un requisito (precedencia de arriba abajo, `today` = fecha actual):
   | Estado | Condición |
   |---|---|
   | `missing` | no existe un documento del tipo |
   | `draft` | el documento está en borrador |
   | `expired` | vigente y `review_date < today` |
   | `unowned` | vigente, no vencido y sin unidad responsable |
   | `in_force` | vigente, al día y con responsable |
   Además cada requisito expone la lista de **issues** (`draft`, `expired`, `unowned`, `missing`) que aplican a la vez.
5. Completitud = requisitos `in_force` / total.
6. Las cláusulas son **dato** (`clause_ref`); la UI avisa que debe verificarse contra la edición de la norma usada.

## Criterios de aceptación
- **AC-005-1** *Given* un usuario autenticado, *When* `GET /pims/requirements`, *Then* 200 con los 11 requisitos en el orden del PLAN, cada uno con cláusula, título, tipo de documento, resumen, evidencia esperada y unidad responsable (código y nombre); sin token → 401.
- **AC-005-2** *Given* los requisitos, *Then* cada uno tiene un tipo `PIMS_*` distinto y no existe un tipo `PIMS_*` sin requisito.
- **AC-005-3** *Given* el seed y la fecha de referencia, *When* `GET /pims/completeness`, *Then* devuelve por requisito su estado, issues y resumen del documento (código, título, versión vigente, ciclo de vida, fecha de revisión, responsable) o `null` si no existe, más totales por estado y el porcentaje de vigentes.
- **AC-005-4** *Given* combinaciones de ciclo de vida, revisión y responsable, *Then* el estado respeta la precedencia de la regla 4 y los issues listan todo lo que aplique (p. ej. un vigente vencido y sin responsable → `expired` con issues `expired` y `unowned`).
- **AC-005-5** *Given* `GET /documents` y `GET /documents/{code}`, *Then* incluyen `lifecycle` y `review_date`.
- **AC-005-6** *Given* el seed, *Then* existen 10 documentos PIMS y 11 requisitos con el reparto sembrado: 5 vigentes, 2 vencidos, 2 borradores, 1 sin responsable y 1 inexistente (monitoreo y medición); ejecutarlo dos veces no duplica; `--reset-documents` lo restaura.
- **AC-005-7** *Given* `content/`, *Then* los requisitos y los documentos PIMS son válidos: tipos conocidos, unidades responsables existentes en el seed de la universidad, `lifecycle` válido y como máximo un documento por tipo PIMS.
- **AC-005-8** *Given* un documento PIMS, *When* un usuario propone un cambio y el superadmin lo aprueba, *Then* funciona como cualquier documento (nueva versión) y el estado del requisito no cambia por ello.
- **AC-005-9** La API expone los paths/métodos de `contracts/openapi.yaml`.
- **AC-005-10** Los cambios cumplen AC-001-5 (sin frameworks en `domain`/`application`).
- **AC-005-11** *Given* la UI, *Then* `/documents/pims` muestra el resumen de completitud, la matriz (cláusula, requisito, estado con texto además de color, documento enlazado o "No existe", responsable, revisión) y la evidencia esperada desplegable; `/documents` muestra el ciclo de vida de cada documento.

## Fuera de alcance
Publicar un borrador (cambiar el ciclo de vida) desde la UI, recordatorios de revisión, ejercicios de las Rutas 2–4 que usan este conjunto (Fase 5), analytics por cláusula (Fase 6).

## Estado sembrado (ficticio)
| # | Cláusula | Documento | Estado |
|---|---|---|---|
| 1 | 4.3 | Alcance del PIMS | vigente |
| 2 | 5.2 | Política de privacidad | vigente |
| 3 | 6.1.2 | Proceso de evaluación de riesgos | **vencido** |
| 4 | 6.1.3 e | Declaración de aplicabilidad | **borrador** |
| 5 | 6.1.3 f | Plan de tratamiento | **sin responsable** |
| 6 | 6.1.3 c | Programa de seguridad (con incidentes) | vigente |
| 7 | 8.2 | Resultados de la evaluación de riesgos | vigente |
| 8 | 8.3 | Resultados del tratamiento | **borrador** |
| 9 | 7.2 | Evidencia de competencia | vigente |
| 10 | 9.1 | Evidencia de monitoreo y medición | **no existe** |
| 11 | 10.2 | No conformidades y acciones correctivas | **vencido** |

Las fechas de revisión de los vigentes están en 2030 y las de los vencidos en 2025, para que el reparto no cambie con el paso del tiempo.
