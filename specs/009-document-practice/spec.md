# Spec 009 — Motor de práctica documental (F8)

**Estado:** aprobada (plan 009+, Fase F8)
**Relacionados:** [plan maestro](../009-practica-real-y-asistentes/plan.md) · [inventario de plantillas](../../docs/practica-documental/inventario-plantillas.md) · [adaptación 27001→27701](../../docs/adaptacion-plantillas-27001-a-27701.md)

---

## Objetivo
Construir el **motor de práctica documental** (backend de dominio puro + generadores UNSA + componentes Svelte accesibles + solucionador del seed) para que las Rutas 2, 3 y 4 puedan ofrecer prácticas serias basadas en la estructura de las 16 plantillas reales de `raw/files/`, con vista lado a lado «ejemplo resuelto / tu documento» y corrección determinista por reglas defendibles.

## Historias
- **H1.** Como participante quiero ver un **ejemplo resuelto de la UNSA** junto al formulario o tabla que debo completar, para entender el estándar esperado sin adivinar formatos.
- **H2.** Como participante quiero practicar con documentos reales adaptados a privacidad (`Alcance`, `Política`, `Cuadro de evaluación y tratamiento de riesgos`, `Plan de tratamiento`, `Matriz de competencia`, `Lista de auditoría`, `Formulario de no conformidades`), recibiendo retroalimentación por campo o fila sobre **qué falló y por qué**.
- **H3.** Como participante que se equivoca repetidamente en un ejercicio complejo quiero obtener orientación concreta tras agotar intentos sin que me regalen la aprobación automática.
- **H4.** Como autor de contenido y evaluador del POC quiero definir ejercicios en JSON declarativo (o generados desde la BD ficticia) con la garantía de que ninguna solución ni regla privada se filtra al navegador y de que el solucionador del seed alcanza 100 puntos en todo ejercicio válido.

## Tipos de ejercicio propuestos (6 nuevos en `ExerciseKind`)

Todos se suman a los 6 existentes (`ordering`, `matching`, `single_choice`, `quiz`, `branching`, `soa_form`) y comparten el contrato común `validate_spec` / `to_public` / `grade` → `GradeResult(score 0..100, items)`.

| Kind | Plantilla(s) origen | Qué practica y qué corrige |
|---|---|---|
| `document_form` | Alcance, Política, Metodología, Informe de riesgos, Minutas de dirección, Programa anual de auditoría, Informe de auditoría | Secciones con campos tipados (`text`, `textarea`, `select`, `multiselect`, `date`, `position`, `reference`). Valida obligatoriedad, formato/catálogo, **rúbrica estructural determinista** para texto libre (`min_words` + criterios conceptuales + anti-patrones prohibidos) y **reglas cruzadas entre campos** (`date_order`, `disjoint`, `requires_if`, `unit_system_coherence`, `count_matches`). |
| `risk_table` | `Apendice_1_Cuadro_de_evaluacion_de_riesgos_ES.xlsx` + Metodología | Filas activo + controles existentes + amenaza + vulnerabilidad + propietario + consecuencia (`0..2`) + probabilidad (`0..2`). El backend **calcula** `riesgo = C + P`, aplica el umbral (`<= 2` aceptable, `>= 3` no aceptable), exige `C = 2` cuando el activo trata datos sensibles (salud/socioeconómicos), impide cruzar el umbral de aceptación aunque exista tolerancia de 1 punto y explica la desviación por fila. |
| `treatment_table` | `Apendice_2_Cuadro_de_tratamiento_de_riesgos_ES.xlsx` + Plan de tratamiento | Por cada riesgo no aceptable (`>= 3`): opción (`controls`, `transfer`, `avoid`, `accept`), control de la SoA, responsable, plazo y valoración residual (`C_res`, `P_res`). El backend calcula `riesgo_residual = C_res + P_res` y valida coherencia opción ↔ SoA ↔ residual (p. ej. `controls` exige control aplicable en SoA; `accept` prohíbe reducir el riesgo o aplicarlo si está vedado; `avoid` lleva residual a `0`; el residual no puede superar al inicial). |
| `audit_checklist` | `Apendice_3_Lista_de_apoyo_auditoria_interna_ES.docx` | Generable desde `pims_requirements` (`clause_ref` como dato) y estado real de `pims-*` en BD (`audit_checklist_from_pims`), o estático. Por ítem: requisito + contexto observado → pregunta pertinente + evidencia a solicitar + veredicto (`conforme`, `observacion`, `no_conformidad`), validando correspondencia estricta evidencia ↔ estado ↔ veredicto. |
| `nonconformity_form` | Procedimiento + `Apendice_Formulario_para_medidas_correctivas_ES.docx` | Casos de no conformidad UNSA: separa **corrección inmediata** de **acción correctiva**, detecta confusión de síntoma con causa raíz o repetición de la corrección como acción, exige `verification_date > implementation_date` (desfase mínimo en días), valida responsable y necesidad de cambio documental. |
| `competence_matrix` | `Plan_de_capacitacion_y_concienciacion_ES.docx` | Filas por cargo UNSA: asigna competencia requerida, capacitación/ruta adecuada, evidencia válida de eficacia (distinta de mera asistencia) y evaluador con segregación de funciones (un auditor no evalúa su propia competencia). |

## Reglas de negocio

1. **Corrección determinista y sin IA:** Toda evaluación (incluidos campos de texto libre) usa reglas explícitas y deterministas en `learning/domain/`. Ningún ejercicio llama a `agy`.
2. **Privacidad de la spec pública (`to_public`):** El JSON enviado al cliente en `GET /modules/{id}` nunca contiene respuestas esperadas (`expected`, `accepted`, `forbidden`, `expected_*`), criterios de rúbrica (`rubric`, `keywords_any`, `keyword_groups`, `forbidden_any`, `min_words`), reglas cruzadas privadas (`cross_rules`) ni explicaciones privadas.
3. **Retroalimentación diagnóstica y política de intentos agotados (`REVEAL_AFTER_ATTEMPTS = 3`):**
   - En los intentos fallidos 1 y 2 (`attempt_number < 3` y `not passed`), la respuesta indica **qué campo/fila/regla falló y por qué** en términos normativos/metodológicos, sin revelar la solución exacta (`solution_revealed = false`, `solution_guide = null`).
   - A partir del intento fallido 3 (`attempt_number >= 3` y `not passed`), `AttemptResponse` activa `solution_revealed = true` y entrega `solution_guide` con orientación concreta por cada ítem incorrecto para desbloquear el aprendizaje. **Nunca** otorga aprobado gratuito: el participante debe corregir y enviar una respuesta que alcance `pass_score`.
4. **Vista lado a lado «ejemplo resuelto / tu documento»:**
   - Un módulo puede declarar `reference_doc: <codigo>` en el frontmatter de `NN-slug.md` (resuelto desde `content/institutional/<codigo>/` en la última `vN.md`) o un archivo hermano `NN-slug.reference.md`.
   - `ModuleResponse` expone `reference: { title, body_md } | null`. En el cliente, cuando `reference` existe, se muestra junto al ejercicio en disposición lado a lado (escritorio) o con pestañas/apilado accesible (móvil).
   - El ejemplo resuelto **siempre** corresponde a un escenario o unidad distinta (o documento institucional de referencia) de modo que no revele las respuestas exactas del ejercicio asignado.
5. **Hechos enriquecidos de la UNSA:** `UniversitySnapshot` amplía sus proyecciones de solo lectura para exponer `unit_code`/`unit_name` en cargos, `data_categories` y `owner_unit_code` en sistemas, `processing_activities` y `expected_evidence`/`summary` en requisitos PIMS, alimentando los generadores de tablas y listas sin acoplar `learning` a las tablas de `university` o `documents`.
6. **Integridad de contenido `raw/`:** El inventario (`docs/practica-documental/inventario-plantillas.md`) se redacta desde cero en español adaptado a ISO 27701/UNSA. `raw/` no se modifica ni versiona.

---

## Criterios de aceptación

- **AC-009-1 (Inventario y no-copia):** *Given* las 16 plantillas de `raw/files/`, *Then* `docs/practica-documental/inventario-plantillas.md` documenta finalidad, secciones/columnas parafraseadas, reglas implícitas, errores frecuentes y ejercicio derivado para las 16 plantillas, sin contradecir `docs/adaptacion-plantillas-27001-a-27701.md` y sin copiar textos ni catálogos literales ni títulos del Anexo A; `raw/` permanece sin cambios ni seguimiento en git.
- **AC-009-2 (Validación de spec y seguridad de `to_public`):** *Given* cualquiera de los 6 nuevos tipos (`document_form`, `risk_table`, `treatment_table`, `audit_checklist`, `nonconformity_form`, `competence_matrix`), *When* se invoca `validate_spec` con specs válidas e inválidas y `to_public(kind, spec, seed)`, *Then* `validate_spec` rechaza definiciones incompletas con `InvalidExerciseSpec` y el resultado de `to_public` no contiene claves ni valores de solución, rúbricas privadas ni explicaciones.
- **AC-009-3 (`document_form`):** *Given* una spec `document_form` con secciones, campos tipados (`text`, `textarea`, `select`, `multiselect`, `date`, `position`, `reference`), rúbrica de texto libre y `cross_rules` (`date_order`, `disjoint`, `requires_if`, `unit_system_coherence`, `count_matches`), *When* se ejecuta `grade`, *Then* la respuesta perfecta puntúa `100`, respuestas con errores típicos fallan exactamente los ítems y reglas cruzadas afectadas con explicación clara, texto corto o con anti-patrón falla la rúbrica, y formas inválidas lanzan `InvalidAnswer` (HTTP 422).
- **AC-009-4 (`risk_table`):** *Given* una `risk_table` con activos sensibles y no sensibles, *When* se ejecuta `grade`, *Then* el backend calcula `riesgo = consecuencia + probabilidad`, exige `consecuencia = 2` en activos con datos sensibles (penalizando cualquier valor menor), rechaza respuestas que crucen el umbral de aceptación (`<= 2` vs `>= 3`) aun con tolerancia `1`, y devuelve retroalimentación explicando la desviación por fila.
- **AC-009-5 (`treatment_table`):** *Given* una `treatment_table` con riesgos `>= 3` y catálogo de controles con estado SoA, *When* se ejecuta `grade`, *Then* valida opción de tratamiento, aplicabilidad y pertinencia del control en la SoA, coherencia de `riesgo_residual = residual_C + residual_P` (prohibiendo que `accept` reduzca el riesgo o que un control aumente el riesgo), responsable y plazo, otorgando crédito parcial y explicando cada inconsistencia.
- **AC-009-6 (`audit_checklist`):** *Given* el generador `audit_checklist_from_pims` sobre `UniversitySnapshot.pims`, *When* se genera la lista y se evalúa con `grade`, *Then* usa `clause_ref` como dato, deriva el veredicto esperado del estado real de los documentos (`in_force` → `conforme`, `unowned` → `observacion`, `draft`/`expired`/`missing` → `no_conformidad`), valida pregunta pertinente y evidencia a solicitar, y actualiza el veredicto esperado si cambia el estado en BD.
- **AC-009-7 (`nonconformity_form`):** *Given* un `nonconformity_form`, *When* se evalúa una respuesta, *Then* distingue corrección de acción correctiva y causa raíz de síntoma, exige `verification_date` posterior a `implementation_date` con el desfase mínimo configurado, valida responsable y cambio documental, y explica el motivo de cada fallo.
- **AC-009-8 (`competence_matrix`):** *Given* una `competence_matrix` sobre cargos de la UNSA, *When* se evalúa la respuesta, *Then* verifica competencia, capacitación/ruta, evidencia de eficacia (rechazando mera asistencia) y segregación del evaluador por fila.
- **AC-009-9 (Política de intentos agotados):** *Given* un usuario que envía intentos fallidos sobre un módulo con ejercicio, *When* envía los intentos 1 y 2 (`score < pass_score`), *Then* `AttemptResponse` devuelve `solution_revealed = false` y `solution_guide = null`; *When* envía el intento 3 (o posterior) aún fallido, *Then* `solution_revealed = true` y devuelve `solution_guide` con guía por ítem sin acreditar el módulo hasta aprobar un intento posterior.
- **AC-009-10 (Ejemplo resuelto y vista lado a lado):** *Given* un módulo con `reference_doc` o `NN-slug.reference.md`, *When* `SyncContent` sincroniza y el cliente consulta `GET /modules/{id}`, *Then* `ModuleResponse` incluye `reference { title, body_md }` y el frontend muestra el panel «Ejemplo resuelto (UNSA)» junto al ejercicio «Tu documento».
- **AC-009-11 (Hechos enriquecidos de UNSA):** *Given* `SqlAlchemyUniversityFacts` y `LearningFacts`, *Then* `UniversitySnapshot` incluye cargos con su unidad, sistemas con categorías de datos, actividades de tratamiento y requisitos PIMS con `expected_evidence` y `summary`.
- **AC-009-12 (Solucionador del seed):** *Given* `seed/solutions.py`, *Then* `solve(kind, spec)` alcanza `100` puntos y `wrong(kind)` obtiene `< pass_score` sin `InvalidAnswer` en los 6 nuevos tipos (además de los 6 existentes).
- **AC-009-13 (Componentes Svelte accesibles):** *Given* los 6 nuevos componentes de ejercicio y la vista lado a lado en `frontend/`, *Then* funcionan por teclado, usan etiquetas explícitas y alertas con `role="alert"`, respetan el tema claro único y superan `svelte-check`, `vitest` y `axe-core` sin violaciones *serious* ni *critical*.
- **AC-009-14 (Recorrido E2E de formulario documental):** *Given* el stack completo en ejecución, *When* corre Playwright E2E, *Then* un participante visualiza un `document_form` junto a su «Ejemplo resuelto (UNSA)», envía primero una respuesta con errores (verificando retroalimentación por campo/regla cruzada) y luego la corrige hasta aprobar (`passed = true`), manteniendo verdes los recorridos E2E previos.
- **AC-009-15 (Arquitectura, migración, contrato y verificación):** *Given* la implementación de F8, *Then* `test_architecture.py` (AC-001-5), `alembic check` (migración `0008`), `test_contract.py` (`specs/009-document-practice/contracts/openapi.yaml`) y `make verify` pasan sin errores.

## Fuera de alcance
- Reescribir o desbloquear los módulos `planned` de las Rutas 2, 3 y 4 (se ejecutan en F9, F10 y F11 respectivamente).
- Evaluación de texto libre con IA / `agy` (siempre determinista).
- Asistentes flotantes IA (F12 y F13).

---

## Ejemplo concreto incluido en el diseño: `document_form` «Documento de alcance del PIMS» (ampliación OBU + FCSA)

Este ejemplo sirve de especificación piloto para verificar reglas de campos, rúbrica de texto libre y reglas cruzadas sobre hechos reales de la UNSA:

- **Escenario público:** La UNSA amplía el Alcance del PIMS (etapa 2) para incorporar la **Oficina de Bienestar Universitario (OBU)** y las prácticas clínicas de la **Facultad de Ciencias de la Salud (FCSA)** (`EENF`, `ENUT`, `EOBS`), que utilizan el **Sistema de Bienestar y Salud** y remiten análisis clínicos a un **laboratorio médico externo contratado**. Las facultades `FIPS`, `FCNF` y `FCHS` continúan fuera en esta etapa y el **Sistema de Planillas y RR. HH.** permanece bajo ámbito de `ORH`.
- **Secciones y campos públicos:**
  1. *Control documental:* `doc_code` (`text`, ej. `PIMS-ALC-002`), `owner_position` (`position`), `approved_by` (`position`), `approval_date` (`date`), `review_date` (`date`).
  2. *Delimitación y roles:* `included_units` (`multiselect`: `OBU`, `FCSA`, `OTI`, `FIPS`, `FCNF`, `FCHS`, `BIBL`), `included_systems` (`multiselect`: `Sistema de Bienestar y Salud`, `Sistema de Planillas y RR. HH.`, `Biblioteca Digital`, `Sistema de Historia Clínica Móvil`), `unsa_role` (`select`: `responsable`, `encargado`, `ninguno`), `external_processor` (`select`: `lab-externo`, `ninguno`, `fcsa-decanato`).
  3. *Exclusiones y criterios de eficacia:* `exclusions_justification` (`textarea`), `effectiveness_criteria` (`textarea`).
- **Reglas de corrección (privadas, eliminadas por `to_public`):**
  - `doc_code`: patrón `^PIMS-ALC-\d{3}$`.
  - `owner_position`: uno de `{Oficial de Protección de Datos Personales, Jefe de la Oficina de Tecnologías de la Información}`.
  - `approved_by`: `Rector`.
  - `approval_date` / `review_date`: fechas ISO válidas; **regla cruzada `date_order`**: `review_date > approval_date` y diferencia ≤ 365 días (revisión al menos anual).
  - **Regla cruzada `disjoint`**: `owner_position != approved_by` (quien elabora/mantiene el alcance no lo autoaprueba como máxima autoridad).
  - `included_units`: obligatorias `{OBU, FCSA, OTI}`, prohibidas `{FIPS, FCNF, FCHS, BIBL}`.
  - `included_systems`: obligatorio `{Sistema de Bienestar y Salud}`, prohibidos sistemas de unidades excluidas o inexistentes (`Sistema de Planillas y RR. HH.`, `Biblioteca Digital`, `Sistema de Historia Clínica Móvil`). **Regla cruzada `unit_system_coherence`**: todo sistema incluido debe pertenecer a una unidad incluida.
  - `unsa_role`: `responsable`. `external_processor`: `lab-externo`.
  - `exclusions_justification` (rúbrica): mínimo 15 palabras; requiere 3 criterios conceptuales (mencionar facultades excluidas o anonimización; justificar incorporación gradual o ausencia de identificabilidad; indicar control en frontera/contrato de encargo con el laboratorio) y rechaza anti-patrones («sin exclusiones», «por costo»).
  - `effectiveness_criteria` (rúbrica): mínimo 10 palabras; requiere 2 criterios (indicador cuantitativo + relación con límites del alcance o incidentes/tratamientos fuera de inventario).

---

## Decisiones confirmadas (2026-11-11)
1. **Ubicación del piloto E2E en F8 (AC-009-14):** Se mantiene sin cambios el conteo actual de R2–R4 (1 módulo publicado por ruta) para no alterar `test_routes_2_4_content.py` ni el cohorte demo antes de F9–F11; se adjunta `04-declaracion-de-aplicabilidad.reference.md` al módulo demo de R3 para probar la vista lado a lado en contenido real, y se ejecuta el E2E de `document_form` contra un módulo temporal insertado y limpiado durante la suite Playwright.
2. **Umbral de revelación de guía en intentos agotados:** Confirmado `REVEAL_AFTER_ATTEMPTS = 3` intentos fallidos (`attempt_number >= 3` y `not passed`), devolviendo `solution_guide` sin aprobar automáticamente.
3. **Nombre de carpeta de spec:** Confirmado `specs/009-document-practice/` siguiendo el formato `001..008`, manteniendo intacto `specs/009-practica-real-y-asistentes/` como hoja de ruta maestra de F8–F13.
