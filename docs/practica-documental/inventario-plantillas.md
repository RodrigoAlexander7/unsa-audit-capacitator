# Inventario estructural de plantillas (`raw/files/`) y adaptación a ISO/IEC 27701

> **Estado:** borrador para aprobación (Fase F8 — A.0).
> **Restricción legal y de autoría:** las 16 plantillas en `raw/files/` son material de terceros con autor acreditado y permanecen fuera del control de versiones. Este documento describe **únicamente su estructura, flujo, reglas implícitas y errores frecuentes**, redactados con palabras propias para adaptarlos a ISO/IEC 27701 (privacidad) y a la UNSA ficticia (POC). No reproduce párrafos, catálogos ni títulos literales de controles del Anexo A.
> Amplía sin contradecir el mapeo de [adaptacion-plantillas-27001-a-27701.md](../adaptacion-plantillas-27001-a-27701.md).

---

## Resumen de cobertura: 16 plantillas → conjunto PIMS y rutas

| # | Archivo en `raw/files/` | Documento PIMS / uso UNSA | Cláusula (dato) | Ruta / tipo de ejercicio derivado |
|---|---|---|---|---|
| 1 | `Documento_sobre_el_alcance_del_SGSI_ES.docx` | 1. Alcance del PIMS (`pims-alcance`) | `4.3` | R2 (`document_form` revisión) · R3 (`document_form` elaboración) |
| 2 | `Politica_de_seguridad_de_la_informacion_ES.docx` | 2. Política de privacidad (`pims-politica-privacidad`) | `5.2` | R2 (`document_form`) · R3 (`document_form`) |
| 3 | `Metodologia_de_evaluacion_y_tratamiento_de_riesgos_ES.docx` | 3. Proceso de evaluación de riesgos (`pims-proceso-riesgos`) | `6.1.2` | R2 (`quiz`/`document_form`) · base normativa de `risk_table` y `treatment_table` |
| 4 | `Apendice_1_Cuadro_de_evaluacion_de_riesgos_ES.xlsx` | 7. Resultados de la evaluación (`pims-resultados-riesgos`) | `8.2` | R3 (`risk_table` con datos UNSA) |
| 5 | `Declaracion_de_aplicabilidad_ES.docx` | 4. Declaración de aplicabilidad (`pims-soa`) | `6.1.3 e` | R2 (`matching`/`document_form`) · R3 (`soa_form` ampliado) |
| 6 | `Plan_de_tratamiento_del_riesgo_ES.docx` | 5. Plan de tratamiento (`pims-plan-tratamiento`) | `6.1.3 f` | R3 (`treatment_table` + `document_form`) |
| 7 | `Apendice_2_Cuadro_de_tratamiento_de_riesgos_ES.xlsx` | 8. Resultados del tratamiento (`pims-resultados-tratamiento`) | `8.3` | R3 (`treatment_table` con riesgo residual) |
| 8 | `Apendice_3_Informe_sobre_evaluacion_y_tratamiento_ES.docx` | Informe consolidado de riesgos (complementa 7 y 8) | `8.2 / 8.3` | R3 (`document_form` informe ejecutivo de riesgos) |
| 9 | `Plan_de_capacitacion_y_concienciacion_ES.docx` | 9. Evidencia de competencia (`pims-competencia`) | `7.2` | R2 (`competence_matrix`) · R3 (`competence_matrix`) |
| 10 | `Minutas_de_Revision_por_parte_de_la_direccion_ES.docx` | Minutas de revisión por la dirección (complemento 12) | `9.3` | R2 (`document_form`) · R3 (`document_form` indicadores/revisión) |
| 11 | `Procedimiento_para_medidas_correctivas_ES.docx` | 11. No conformidades y acciones correctivas (`pims-no-conformidades`, marco) | `10.2` | Base normativa de `nonconformity_form` en R3/R4 |
| 12 | `Apendice_Formulario_para_medidas_correctivas_ES.docx` | 11. Ficha operativa de medida correctiva (`pims-no-conformidades`) | `10.2` | R3 (`document_form` registros) · R4 (`nonconformity_form`) |
| 13 | `Procedimiento_para_auditoria_interna_ES.docx` | Marco de auditoría interna (ISO 19011 en UNSA) | `9.2` | R4 (`document_form` plan/criterios + reglas de imparcialidad) |
| 14 | `Apendice_1_Programa_anual_de_auditoria_interna_ES.docx` | Programa anual de auditoría interna | `9.2` | R4 (`document_form` programa anual) |
| 15 | `Apendice_2_Informe_de_auditoria_interna_ES.docx` | Informe de auditoría interna | `9.2` | R4 (`document_form` informe y seguimiento) |
| 16 | `Apendice_3_Lista_de_apoyo_auditoria_interna_ES.docx` | Lista de verificación de auditoría interna | `9.2` | R4 (`audit_checklist` generado desde `pims_requirements`) |

> **Nota de completitud:** Dos documentos del §5 del PLAN no tienen plantilla directa en `raw/files/`: (a) **Programa de seguridad e incidentes** (`pims-programa-seguridad`, `6.1.3 c`) y (b) **Evidencia de monitoreo y medición** (`pims-monitoreo`, `9.1`, ausente a propósito en la BD inicial para simular brecha auditable). En ambos casos se usan las estructuras propias definidas en `content/institutional/` y en las minutas/informes de revisión.

---

## Cadena de trazabilidad entre plantillas

```
[1. Alcance] ──► [2. Política]
     │                 │
     ▼                 ▼
[3. Metodología] ──► [4. Cuadro evaluación riesgos] ──► [7. Cuadro tratamiento] ──► [5. SoA + residuales]
                           │                                   │                            │
                           └───────────► [8. Informe riesgos] ◄┴──► [6. Plan tratamiento] ──┤
                                                                                            ▼
[9. Capacitación/Competencia] ◄──► [10. Minutas dirección] ◄──► [13–16. Auditoría interna] ──► [11–12. Medidas correctivas]
```

Cada flecha representa una regla de consistencia verificable de forma determinista por el motor de ejercicios (por ejemplo: ningún sistema fuera del alcance debe aparecer sin justificación en el informe; todo riesgo `>= 3` en evaluación debe tener fila en tratamiento; todo control elegido en tratamiento debe estar marcado como aplicable en la SoA; toda no conformidad del informe de auditoría debe tener referencia cruzada al formulario de medidas correctivas).

---

## Detalle estructural por plantilla

### 1. Documento sobre el alcance (`Documento_sobre_el_alcance_del_SGSI_ES.docx`)
- **Finalidad:** Fijar con precisión las fronteras organizativas, geográficas, de procesos y tecnológicas cubiertas por el sistema de gestión, así como lo excluido y el traslado de responsabilidad en las fronteras.
- **Secciones y campos (parafraseados):**
  1. *Control del documento:* código, versión, fecha de vigencia, autor, aprobador, nivel de reserva e historial de cambios.
  2. *Propósito, aplicación y destinatarios:* delimitación del objeto y públicos internos/externos que lo usan.
  3. *Referencias:* cláusula de alcance, marco legal/contractual y plan de implantación.
  4. *Definición operativa en cinco ejes:*
     - Procesos y servicios incluidos.
     - Unidades organizativas incluidas y su separación respecto a las excluidas.
     - Sedes/ubicaciones físicas cubiertas y fronteras físicas.
     - Redes e infraestructura TIC dentro del perímetro.
     - Exclusiones explícitas y su justificación.
  5. *Vigencia y criterios de eficacia:* fecha límite de validez, cargo propietario, periodicidad de revisión e indicadores de adecuación (incidentes o correcciones derivadas de un límite ambiguo).
  6. *Firma de aprobación.*
- **Adaptación 27701 / UNSA:** Añade la columna/eje de **actividades de tratamiento de datos personales**, el catálogo real de **sistemas de la UNSA**, la distinción **responsable vs. encargado** por tratamiento y el detalle de encargados externos (respaldos en nube o laboratorios). Referencia resuelta base: `content/institutional/pims-alcance/v1.md`.
- **Reglas implícitas:**
  - Coherencia unidades ↔ sistemas: todo sistema incluido debe corresponder a unidades incluidas o de soporte (`OTI`).
  - La aprobación corresponde a alta dirección (`Rector`), no solo al coordinador técnico.
  - Fecha de revisión ≥ fecha de aprobación y periodicidad ≤ 1 año.
  - Las exclusiones deben ser acotadas y justificadas (no pueden ocultar tratamientos sensibles activos dentro de la unidad cubierta).
- **Errores típicos:** Declarar cobertura «total» de la universidad cuando facultades/escuelas están fuera; citar sistemas inexistentes o de otras oficinas excluidas; olvidar el rol (`controller`/`processor`) y los encargados externos; dejar el documento sin fecha de revisión o autoaprobado.
- **Ejercicio derivado:** `document_form` en **R2 01** (auditar y completar fronteras de alcance) y en **R3** (elaborar el alcance de una ampliación/oficina UNSA con reglas cruzadas contra el organigrama y catálogo de sistemas).

### 2. Política de privacidad (`Politica_de_seguridad_de_la_informacion_ES.docx`)
- **Finalidad:** Expresar el compromiso formal de la alta dirección con la protección de la información/datos personales, definir principios, marco de objetivos, cumplimiento normativo, asignación de responsabilidades y respaldo de recursos.
- **Secciones y campos (parafraseados):**
  1. *Control e historial.*
  2. *Objetivo, alcance y usuarios:* alineación al documento de alcance y cobertura a personal y terceros.
  3. *Referencias y glosario esencial:* conceptos base del sistema de gestión.
  4. *Bloque de gobierno y gestión:*
     - Objetivos generales, responsables de definirlos, revisarlos y medir su cumplimiento al menos anualmente.
     - Compromiso con obligaciones legales, regulatorias y contractuales.
     - Enlace con la selección de controles (metodología y SoA) y continuidad operativa.
     - Reparto de responsabilidades por rol (dirección, coordinación operativa, dueños de activos, notificación de incidentes, capacitación, comunicación).
     - Mecanismo de difusión interna y externa.
  5. *Declaración de apoyo y provisión de recursos.*
  6. *Vigencia, propietario, indicadores de eficacia y aprobación.*
- **Adaptación 27701 / UNSA:** Reemplaza los conceptos genéricos por los **principios de tratamiento de datos personales** (licitud, finalidad, minimización, exactitud, conservación limitada, seguridad, responsabilidad proactiva), **derechos de los titulares (ARCO)**, reglas reforzadas para **datos sensibles**, gestión de **encargados y transferencias**, y notificación de **brechas al DPO**. Referencia resuelta base: `content/institutional/pims-politica-privacidad/v1.md`.
- **Reglas implícitas:**
  - Debe emitirla/aprobarla la máxima autoridad (`Rector`), nunca una jefatura operativa aislada.
  - Debe mantener un nivel estratégico (principios, roles y marco de objetivos), sin incrustar detalles técnicos volátiles (p. ej. longitud de contraseñas).
  - Separación de roles entre autoridad aprobadora (`Rector`), vigilancia/titulares (`DPO`), operación (`CISO`/`OTI`) y custodia por unidad (`Jefes de unidad`).
- **Errores típicos:** Copiar una política genérica sin mencionar derechos de titulares ni datos sensibles; mezclar procedimientos operativos detallados dentro de la política; omitir el canal de reporte de incidentes o el mecanismo de difusión y revisión anual.
- **Ejercicio derivado:** `document_form` en **R2 02** (verificar elementos obligatorios y responsables) y **R3 05** (completar/adecuar política y procedimientos para una oficina/etapa de la UNSA).

### 3. Metodología de evaluación y tratamiento de riesgos (`Metodologia_de_evaluacion_y_tratamiento_de_riesgos_ES.docx`)
- **Finalidad:** Definir reglas repetibles y objetivas para identificar activos y riesgos, valorarlos, establecer el umbral de aceptabilidad, seleccionar opciones de tratamiento y gobernar los registros resultantes.
- **Secciones y campos (parafraseados):**
  1. *Control e historial; propósito, alcance y usuarios.*
  2. *Documentos de referencia.*
  3. *Método de evaluación:* inventario de activos y sus propietarios → identificación de amenazas y vulnerabilidades → asignación de propietarios de riesgo → escala de consecuencias (`0`, `1`, `2`) → escala de probabilidad (`0`, `1`, `2`, según eficacia de controles vigentes) → cálculo por suma (`R = C + P`).
  4. *Criterio de aceptación:* niveles `0–2` aceptables; niveles `3–4` no aceptables (tratamiento obligatorio).
  5. *Método de tratamiento:* traslado desde el cuadro de evaluación de los riesgos `>= 3`; cuatro opciones (controles, transferencia, evitación, aceptación excepcional por costo/impacto); valoración del riesgo residual; enlace a SoA, Plan de tratamiento e Informe anual.
  6. *Control de registros generados:* tabla con nombre del registro, ubicación, custodio, protección contra edición indebida y retención.
  7. *Vigencia, periodicidad de revisión (anual o ante cambios mayores), indicadores de eficacia del método y aprobación.*
- **Adaptación 27701 / UNSA:** La escala de consecuencia incorpora el **impacto sobre los titulares**; regla institucional UNSA (`pims-proceso-riesgos/v1.md`): **si el tratamiento involucra datos sensibles (salud, socioeconómicos), la consecuencia es siempre `2`**. Los activos abarcan tanto `systems` como `processing_activities`.
- **Reglas implícitas:**
  - `riesgo = consecuencia + probabilidad` (`0..4`), umbral de aceptación `<= 2`.
  - La probabilidad inicial evalúa **controles actualmente vigentes**, no controles planeados.
  - «Aceptar» un riesgo no aceptable exige demostrar desproporción costo/impacto y no puede usarse para incumplir mandatos legales de privacidad.
  - El propietario del riesgo puede ser distinto del propietario del activo, pero ambos deben tener autoridad sobre el proceso/sistema.
- **Errores típicos:** Evaluar probabilidad baja contando controles futuros aún no implantados; poner consecuencia `0` o `1` en sistemas con historias clínicas o datos bancarios; usar fórmula multiplicativa sobre escala aditiva o inventar umbrales incompatibles con la metodología vigente.
- **Ejercicio derivado:** Reglas de dominio de `risk_table` y `treatment_table`; `document_form` / `quiz` en **R2 03** para dominar el criterio antes de aplicarlo en R3.

### 4. Cuadro de evaluación de riesgos (`Apendice_1_Cuadro_de_evaluacion_de_riesgos_ES.xlsx`)
- **Finalidad:** Aplicar operativamente la metodología sobre cada activo del alcance, calculando el nivel de riesgo y dejando trazabilidad de controles existentes.
- **Hojas y columnas (parafraseadas):**
  - *Hoja 1 — Matriz de evaluación:* período de aplicación (`desde… hasta…`) y tabla con 10 columnas: correlativo, activo, propietario del activo, amenaza, vulnerabilidad, propietario del riesgo, consecuencia (`0..2`), probabilidad (`0..2`), nivel de riesgo (fórmula suma `consecuencia + probabilidad`), controles existentes.
  - *Hoja 2 — Taxonomía referencial de activos:* 6 grandes categorías (personas, aplicaciones/bases de datos, documentación, equipamiento TIC, infraestructura física, servicios tercerizados).
  - *Hoja 3 — Catálogo referencial de amenazas:* lista de amenazas humanas, de software/red, legales/contractuales y físicas/ambientales.
  - *Hoja 4 — Catálogo referencial de vulnerabilidades:* lista de debilidades técnicas, de control de acceso, operativas, organizacionales y físicas.
- **Adaptación 27701 / UNSA:** Los activos provienen de `systems` y `processing_activities` de la UNSA; los propietarios de `positions`; los catálogos de amenazas y vulnerabilidades se redactan desde cero centrados en datos personales (sin copiar los listados originales). Referencia resuelta: `content/institutional/pims-resultados-riesgos/v1.md`.
- **Reglas implícitas:**
  - `riesgo = consecuencia + probabilidad`; todo riesgo `>= 3` es no aceptable y debe pasar al Cuadro de tratamiento.
  - Regla de datos sensibles: `datos de salud` / `datos socioeconómicos` → `consecuencia == 2`.
  - Coherencia entre controles existentes y probabilidad: si los controles descritos son nulos o rotos (p. ej. cuentas compartidas o base sin cifrar), probabilidad no puede ser `0`.
  - Distinción estricta entre *amenaza* (evento/actor que puede dañar) y *vulnerabilidad* (debilidad del activo/control explotable).
- **Errores típicos:** Invertir amenaza y vulnerabilidad; subestimar consecuencia en datos sensibles; poner probabilidad `0` cuando hay debilidad evidente; asignar propietario de riesgo de otra oficina sin injerencia.
- **Ejercicio derivado:** **`risk_table`** (R3 03): evaluación de escenarios sobre activos reales de la UNSA con cálculo automático en backend, detección de desviaciones frente al umbral y validación de la regla de datos sensibles.

### 5. Declaración de aplicabilidad — SoA (`Declaracion_de_aplicabilidad_ES.docx`)
- **Finalidad:** Declarar qué controles son aplicables o excluidos, por qué, qué objetivo persiguen, cómo se implementan y en qué estado están, además de formalizar la aceptación de riesgos residuales.
- **Secciones y campos (parafraseados):**
  1. *Control, historial, objetivo, alcance, usuarios y referencias.*
  2. *Tabla de aplicabilidad de controles (7 columnas):* identificador del control, tema/descripción del control, aplicabilidad (`Sí/No`), justificación de inclusión o exclusión, objetivo de control, método o documento de respaldo, estado de implementación.
  3. *Aceptación de riesgos residuales:* regla de aceptación automática para riesgos `0–2` más tabla específica de excepción para riesgos residuales `>= 3` que persisten tras los controles (activo, propietario, amenaza, vulnerabilidad, consecuencia residual, probabilidad residual, riesgo residual).
  4. *Vigencia, propietario, criterios de adecuación y firma de aprobación.*
- **Adaptación 27701 / UNSA:** Usa un catálogo propio y parafraseado de temas de control de privacidad y seguridad (separando deberes de `controller`, `processor` y controles transversales), conservando método/documento de respaldo, estado real y la sección de aceptación de riesgos residuales (`content/institutional/pims-soa/v1.md` funciona como borrador con defectos auditables para R4; R3 requiere versión completa y coherente).
- **Reglas implícitas:**
  - Coherencia SoA ↔ Tratamiento: cualquier control usado en el Plan/Cuadro de tratamiento debe figurar como `Sí aplica` en la SoA.
  - Justificación fáctica no circular; exclusión solo válida cuando el rol o naturaleza del tratamiento no ocurre.
  - El estado (`Implementado / Parcial / Planificado`) debe reflejar la evidencia real (no puede decir `Implementado` si el documento soporte está en borrador o no existe).
  - Riesgos residuales `>= 3` no pueden quedar ocultos: deben figurar en la tabla de aceptación excepcional firmada por alta dirección o volver a tratamiento.
- **Errores típicos:** Excluir controles obligatorios por rol; justificar con «porque aplica la norma»; declarar `Implementado` sin evidencia; omitir la aceptación de riesgos residuales `>= 3`.
- **Ejercicio derivado:** **`soa_form`** (ya existe en R3 04 y se enriquece en F10 con método/estado/aceptación residual) y `document_form` en **R2 04** (interpretación de aplicabilidad y trazabilidad).

### 6. Plan de tratamiento del riesgo (`Plan_de_tratamiento_del_riesgo_ES.docx`)
- **Finalidad:** Operativizar las acciones derivadas de la evaluación/tratamiento asignando recursos, responsables, fechas, necesidades de capacitación y método de verificación de resultados.
- **Secciones y campos (parafraseados):**
  1. *Cabecera y propósito.*
  2. *Tabla operativa (7 columnas):* descripción de la actividad, recursos generales/financieros requeridos, cargo/persona responsable, fechas de inicio y fin, capacitación/concienciación vinculada, método para evaluar resultados, estado de ejecución.
  3. *Aprobación por la dirección / propietarios de riesgo.*
- **Adaptación 27701 / UNSA:** Enlaza cada actividad con un riesgo no aceptable y un control del catálogo propio de la SoA, usando cargos del organigrama UNSA y vinculando la capacitación con las rutas de la plataforma (`pims-plan-tratamiento/v1.md` presenta ausencias deliberadas para auditar en R4).
- **Reglas implícitas:**
  - Todo riesgo `>= 3` tratado con controles o transferencia debe traducirse en al menos una actividad del plan.
  - `fecha_inicio <= fecha_fin`; ninguna fila aprobada puede quedar sin responsable ni sin método de evaluación de eficacia.
  - Coherencia con el Plan de capacitación si la actividad involucra concienciación o formación técnica.
- **Errores típicos:** Dejar filas «por definir»; fijar plazos sin recursos ni método de comprobación; desalinear responsables frente a la unidad dueña del riesgo o sistema; no enlazar la actividad con la SoA.
- **Ejercicio derivado:** `document_form` combinado o secuencial con **`treatment_table`** en **R3 06**.

### 7. Cuadro de tratamiento de riesgos (`Apendice_2_Cuadro_de_tratamiento_de_riesgos_ES.xlsx`)
- **Finalidad:** Decidir la estrategia para cada riesgo no aceptable, seleccionar los controles pertinentes y recalcular el riesgo residual posterior al tratamiento.
- **Hojas y columnas (parafraseadas):**
  - *Hoja 1 — Matriz de tratamiento (14 columnas en 4 bloques):*
    1. Riesgo heredado: correlativo, activo, propietario del activo, amenaza, vulnerabilidad, propietario del riesgo.
    2. Valoración previa: consecuencia, probabilidad y riesgo inicial (`>= 3`).
    3. Tratamiento: opción seleccionada y controles/medios de implementación.
    4. Valoración residual: nueva consecuencia, nueva probabilidad y riesgo residual calculado (`= nueva_C + nueva_P`).
  - *Hoja 2 — Opciones:* las 4 opciones estándar (aplicar controles, transferir a terceros, evitar el riesgo, aceptar el riesgo).
  - *Hoja 3 — Catálogo de controles:* en el original reproduce los controles de Anexo A (que **no** se copian; se reemplazan por temas de control de privacidad/seguridad propios de la UNSA).
- **Adaptación 27701 / UNSA:** Adapta las opciones a privacidad (p. ej., la transferencia mediante contrato de encargo o seguro no libera al *controller* de su responsabilidad frente a titulares; no cabe «aceptar» un incumplimiento legal directo). Referencia resuelta base: `pims-resultados-tratamiento` (versión completa para R3; la versión borrador de `content/institutional/` sirve para auditar en R4).
- **Reglas implícitas:**
  - `riesgo_residual = nueva_C + nueva_P`.
  - Coherencia opción ↔ control ↔ residual:
    - *Controles*: exige control aplicable en SoA y pertinente al riesgo; normalmente reduce la probabilidad manteniendo la consecuencia si los datos siguen siendo sensibles; `residual_C <= inicial_C` y `residual_P <= inicial_P`.
    - *Aceptar*: sin control nuevo, `riesgo_residual == riesgo_inicial`, solo permitido cuando el costo de mitigar supera el impacto y sin vulnerar deberes legales.
    - *Evitar*: elimina la actividad/dato, llevando el riesgo residual a `0`.
    - *Transferir*: requiere acuerdo/contrato/póliza con tercero; reduce impacto financiero o parte operativa pero no anula a cero la exposición residual de cumplimiento del responsable.
- **Errores típicos:** Reducir el riesgo residual a `0` al aplicar una medida parcial; elegir «Aceptar» para evitar trabajo sobre un riesgo nivel 4 con datos médicos; referenciar controles excluidos en la SoA; ignorar un residual que sigue siendo `>= 3`.
- **Ejercicio derivado:** **`treatment_table`** (R3 06): selección de opción, control SoA compatible, responsable, plazo y cálculo/validación de riesgo residual.

### 8. Informe sobre evaluación y tratamiento de riesgos (`Apendice_3_Informe_sobre_evaluacion_y_tratamiento_ES.docx`)
- **Finalidad:** Consolidar en un informe ejecutivo dirigido a la alta dirección el resumen de quién ejecutó la evaluación y tratamiento, en qué período, bajo qué alcance y metodología, y con qué documentos de respaldo.
- **Secciones y campos (parafraseados):**
  1. *Control, historial, propósito, alcance general y destinatarios.*
  2. *Referencias (cláusulas 8.2/8.3, alcance, política, metodología).*
  3. *Resumen del proceso:* objetivo de evaluación y tratamiento; unidades organizativas cubiertas; fechas de evaluación, de tratamiento y de emisión; responsable líder, participantes/entrevistas con dueños de activos y apoyos externos; síntesis metodológica (escalas `0..2`, suma, umbral `3–4`, cálculo residual); relación de apéndices generados (Cuadros 1 y 2).
  4. *Validez, propietario del informe, apéndices y firma.*
- **Adaptación 27701 / UNSA:** Incluye al DPO junto al responsable de seguridad, alinea las unidades entrevistadas exactamente con `pims-alcance` (6 oficinas centrales en etapa 1) y exige reportar explícitamente cuántos riesgos no aceptables quedaron abiertos o con residual `>= 3`.
- **Reglas implícitas:**
  - Cronología coherente: período de evaluación ≤ período de tratamiento ≤ fecha de informe ≤ fecha de validez.
  - Consistencia estricta entre las unidades declaradas en el informe y las del Alcance del PIMS.
  - Debe citar los resultados reales de los Apéndices 1 y 2 (sin contradecir conteos de riesgos).
- **Errores típicos:** Reportar facultades excluidas como evaluadas; fechar el informe antes de concluir el tratamiento; omitir a los propietarios de activos en el levantamiento; omitir riesgos residuales aún no aceptables.
- **Ejercicio derivado:** `document_form` (R3 06/08): redactar y validar el Informe ejecutivo de evaluación y tratamiento de riesgos de la UNSA con verificación cronológica y de consistencia contra Alcance y Cuadros.

### 9. Plan de capacitación y concienciación (`Plan_de_capacitacion_y_concienciacion_ES.docx`)
- **Finalidad:** Planificar y evidenciar que cada rol con funciones en el sistema cuenta con las competencias necesarias, recibe concienciación continua y logra los objetivos formativos previstos.
- **Secciones y campos (parafraseados):**
  1. *Cabecera estándar.*
  2. *Matriz de competencias y formación (6 columnas):* cargo o persona, conocimientos/habilidades requeridos, capacitación necesaria, registro de realización, verificación de logro de objetivos (eficacia) y competencias/experiencia alcanzadas.
  3. *Calendario anual de concienciación:* métodos continuos (jornada informativa, inducción, formación periódica, intranet, boletín, reuniones, e-learning, correos, videos) distribuidos por meses (enero–diciembre).
  4. *Asignación de responsabilidades:* quién coordina, quién custodia registros, quién evalúa eficacia y quién mantiene y archiva el plan (ubicación y plazo de retención).
- **Adaptación 27701 / UNSA:** Conecta los cargos del organigrama UNSA (`Rector`, `Jefe OTI`, `DPO`, `CISO`, `Jefe ORA`, `Jefe OBU`, `Jefe ORH`, `Auditores internos`) con las competencias de privacidad y las 4 rutas de la plataforma, separando constancia de asistencia de evaluación objetiva de eficacia (≥ 70 %). Referencia: `content/institutional/pims-competencia/v1.md`.
- **Reglas implícitas:**
  - Cargos críticos (DPO, CISO, custodios de datos sensibles y auditores) requieren formación especializada más allá de la sensibilización básica.
  - Registro de asistencia ≠ evidencia de eficacia: la cláusula `7.2` exige evaluar si la formación cerró la brecha.
  - Segregación: `ORH` coordina y archiva, los especialistas/DPO validan idoneidad técnica y un auditor interno no certifica su propia competencia.
- **Errores típicos:** Aceptar una hoja de asistencia como única prueba de competencia; asignar solo Ruta 1 al DPO o a auditores internos; dejar sin responsable la evaluación de eficacia; omitir al personal que maneja datos de salud o planillas.
- **Ejercicio derivado:** **`competence_matrix`** (R2 07 y R3 07 / R4 09): asignar competencias, rutas formativas, evidencias válidas de eficacia y evaluador sin conflicto de interés por cargo de la UNSA.

### 10. Minutas de revisión por parte de la dirección (`Minutas_de_Revision_por_parte_de_la_direccion_ES.docx`)
- **Finalidad:** Registrar las reuniones periódicas de la alta dirección donde se evalúan las entradas obligatorias del sistema de gestión y se acuerdan decisiones de mejora, cambios y asignación de recursos.
- **Secciones y campos (parafraseados):**
  1. *Datos de la sesión:* órgano directivo, fecha, lista de asistentes y propósito.
  2. *Entradas revisadas (11 bloques):* informes de auditoría interna/externa y de proveedores; feedback de partes interesadas; nuevos métodos/buenas prácticas; informe y avance del plan de tratamiento de riesgos; estado de no conformidades y acciones correctivas; resultados de medición/monitoreo y cumplimiento de objetivos; seguimiento de acuerdos de revisiones previas; cambios internos/externos relevantes; recomendaciones de mejora (incluyendo cambios a política/objetivos); resultados de pruebas/simulacros y revisiones post-incidente.
  3. *Decisiones y salidas (8 bloques):* ajustes al alcance; acciones de mejora de eficacia; actualización de evaluación de riesgos y planes; cambios en documentación y controles; recursos aprobados; necesidades presupuestales; mejoras a indicadores de eficacia; partes interesadas a notificar.
  4. *Cierre y firma directiva.*
- **Adaptación 27701 / UNSA:** Sesión del Rectorado / Comité Directivo del PIMS con participación de dirección y DPO; incorpora como entradas específicas el estado de solicitudes de titulares (ARCO), brechas de datos, documentos vencidos/borradores de la matriz PIMS (`pims-monitoreo` faltante, `pims-soa` borrador) y resultados de capacitación.
- **Reglas implícitas:**
  - Debe existir correspondencia entre **entradas problemáticas** y **salidas/decisiones** (si un indicador falta o una NC está vencida, debe existir una decisión asignando recursos/plazo/responsable).
  - Requiere participación de alta dirección (`Rector` / `Vicerrectores`), no solo reunión técnica de `OTI`.
  - Las decisiones de cambio normativo/alcance se materializan mediante solicitudes de cambio (`change_requests`).
- **Errores típicos:** Redactar actas vacías («se revisó todo sin novedades»); no tratar los resultados de monitoreo faltantes o documentos caducos; aprobar cambios sin presupuesto ni responsable; realizar la revisión sin presencia directiva.
- **Ejercicio derivado:** `document_form` (R2 07 y R3 08): completar/auditar una Minuta de Revisión por la Dirección ante hallazgos e indicadores reales de la UNSA, validando cobertura de entradas obligatorias y coherencia con decisiones/recursos.

### 11. Procedimiento para medidas correctivas (`Procedimiento_para_medidas_correctivas_ES.docx`)
- **Finalidad:** Establecer el flujo obligatorio para contener no conformidades, investigar causas raíz, implementar acciones correctivas, verificar eficacia y actualizar la documentación del sistema.
- **Secciones y campos (parafraseados):**
  1. *Control, historial, objetivo, alcance, usuarios y referencias.*
  2. *Marco conceptual:* definición de no conformidad (incumplimiento de norma, ley, contrato o regla interna), **corrección** (contención inmediata del efecto) y **acción correctiva** (eliminación de la causa raíz para prevenir recurrencia).
  3. *Flujo de 9 pasos con responsable asignado:* detección → análisis de causa raíz → búsqueda de antecedentes similares → evaluación de necesidad de acción correctiva → definición de acciones → ejecución → verificación de eficacia → comunicación a partes afectadas → actualización documental si procede.
  4. *Control de registros, validez, indicadores de eficacia del proceso y firma.*
- **Adaptación 27701 / UNSA:** Incluye fuentes de privacidad (reclamos de titulares por plazos ARCO, brechas, hallazgos de auditoría interna PIMS) y conecta la actualización documental con el flujo de *change requests* de la plataforma. Referencia: `content/institutional/pims-no-conformidades/v1.md`.
- **Reglas implícitas:**
  - Separación estricta entre corrección inmediata y acción correctiva sobre la causa raíz.
  - Quien verifica la eficacia comprueba resultados después de implementada la acción, idealmente con independencia del ejecutor.
  - La recurrencia de una no conformidad obliga a revisar si la causa raíz anterior fue mal diagnosticada.
- **Errores típicos:** Confundir corrección con acción correctiva; atribuir la causa al «error humano» sin detectar la falla de proceso/control; cerrar en el acto sin verificar eficacia en el tiempo.
- **Ejercicio derivado:** Base de reglas del tipo **`nonconformity_form`** en **R3 07** y **R4 07**.

### 12. Formulario para medidas correctivas (`Apendice_Formulario_para_medidas_correctivas_ES.docx`)
- **Finalidad:** Registrar de forma individual y auditable cada no conformidad y el ciclo completo hasta su cierre eficaz.
- **Campos del formulario (12 filas parafraseadas):**
  1. Número identificador de medida correctiva.
  2. Descripción objetiva de la no conformidad.
  3. Proceso/lugar donde se detectó, nombre del detector y firma.
  4. Causa raíz identificada.
  5. Referencia cruzada a no conformidad similar previa (si existía).
  6. Decisión explícita: ¿requiere acción correctiva? (`Sí/No`).
  7. Descripción de la acción correctiva a ejecutar.
  8. Destinatarios que deben ser informados tras la ejecución.
  9. Aprobador, fecha límite y responsable de implementación.
  10. Fecha efectiva de implementación y firma.
  11. Fecha de revisión de eficacia y firma de verificación.
  12. Cambios requeridos en documentos del sistema de gestión y firma.
- **Adaptación 27701 / UNSA:** Añade campo explícito de **corrección inmediata** (para forzar al participante a separarla de la acción correctiva), impacto en titulares y referencia a documentos `pims-*` / institucionales de la UNSA.
- **Reglas implícitas:**
  - `correccion != accion_correctiva`: la corrección resuelve el caso puntual; la acción correctiva modifica proceso/control/capacitación para atacar la `causa_raiz`.
  - Cronología: `fecha_deteccion <= fecha_implementacion < fecha_verificacion_eficacia` (la eficacia no se verifica el mismo día que se implementa).
  - Si se declara una falla de procedimiento o rol ausente, debe marcarse que requiere cambio documental apuntando al documento correcto.
- **Errores típicos:** Repetir la corrección en el campo de acción correctiva; describir la causa como el mismo síntoma; fijar fecha de verificación igual o anterior a la implementación; olvidar actualizar el procedimiento afectado.
- **Ejercicio derivado:** **`nonconformity_form`** (R4 07, y aplicable en R3 07) sobre casos reales de la UNSA (`NC-02` baja de cuentas ORH→OTI, `NC-03` solicitud ARCO fuera de plazo, o hallazgos del borrador de SoA).

### 13. Procedimiento para auditoría interna (`Procedimiento_para_auditoria_interna_ES.docx`)
- **Finalidad:** Normar el ciclo completo de auditorías internas: programación anual basada en riesgos, designación imparcial de auditores, ejecución de auditorías individuales, reporte y enlace con medidas correctivas.
- **Secciones y campos (parafraseados):**
  1. *Control, historial, objetivo, alcance, usuarios y referencias.*
  2. *Objetivos de la auditoría interna:* verificar conformidad (normativa, legal e interna) y eficacia operativa.
  3. *Planificación anual:* aprobación directiva, cobertura acumulativa anual del alcance según riesgos y antecedentes, ejecución previa a la revisión por la dirección, elementos mínimos de cada auditoría.
  4. *Designación de auditores:* criterios de competencia (normas, técnicas de auditoría, conocimiento TIC/procesos) y **regla de imparcialidad / conflicto de interés** (prohibición de auditar el trabajo propio).
  5. *Ejecución individual:* insumos obligatorios (criterios, informes previos, riesgos, lista de apoyo) y salidas (informe de auditoría + formularios de medidas correctivas).
  6. *Control de registros (solo lectura, retención 3 años), validez, criterios de adecuación y firma.*
- **Adaptación 27701 / UNSA:** Incorpora principios de ISO 19011, competencias de privacidad (`controller/processor`, derechos ARCO, datos sensibles) y reglas estrictas de segregación en la UNSA (p. ej. el Jefe de OTI, CISO o DPO no auditan controles ni documentos de la OTI; el Jefe de ORA no audita Matrícula/Notas).
- **Reglas implícitas:**
  - Independencia obligatoria: `unidad(auditor) != unidad(alcance_auditado)` y `auditor != propietario_documento`.
  - Enfoque basado en riesgos: las áreas con riesgos nivel `3–4` o documentos vencidos/borrador tienen prioridad en la programación.
  - La auditoría interna debe completarse antes de la Revisión por la Dirección (`9.3`).
- **Errores típicos:** Nombrar al DPO o Jefe de OTI como auditor de la SoA o del Programa de Seguridad; auditar todas las oficinas por igual ignorando dónde están los datos sensibles y riesgos críticos; omitir el enlace entre hallazgos y medidas correctivas.
- **Ejercicio derivado:** `document_form` en **R4 03** (Plan de auditoría y criterios) + reglas de imparcialidad en **R4 01** y **R4 09**.

### 14. Programa anual de auditoría interna (`Apendice_1_Programa_anual_de_auditoria_interna_ES.docx`)
- **Finalidad:** Planificar el calendario anual de auditorías internas asegurando cobertura de todo el alcance del PIMS con criterios, métodos y auditores independientes.
- **Secciones y columnas (parafraseadas):**
  1. *Cabecera, período anual (`desde… hasta…`) y marco de normas.*
  2. *Tabla de programación (6 columnas):* período/fechas de la auditoría, alcance (unidades/procesos/requisitos), criterios de auditoría (normas, leyes, documentos internos), métodos (revisión documental, entrevistas, muestreo de registros/sistemas), equipo auditor (líder y auditores), registro de ejecución efectiva.
  3. *Aprobación formal.*
- **Adaptación 27701 / UNSA:** Cubre las 6 oficinas del alcance (`ORA`, `BIBL`, `OTI`, `SGEN`, `ORH`, `OBU`) y los 11 requisitos PIMS, integrando criterios ISO 27701/27001 + normativa institucional UNSA + Ley 29733 (complemento), con verificación de no conflicto de intereses por fila.
- **Reglas implícitas:**
  - Cobertura acumulativa del 100 % de unidades y requisitos dentro del año.
  - Priorización de fechas según criticidad/riesgo (p. ej. `OBU` salud y `ORA` notas o `OTI` con documentos vencidos/faltantes).
  - Ningún auditor asignado a una fila puede pertenecer o ser propietario de la unidad/sistema auditado en esa fila.
  - Los métodos deben combinar revisión documental con muestreo de registros/sistemas (no solo entrevistas).
- **Errores típicos:** Dejar oficinas del alcance sin programar; asignar al responsable de la unidad como auditor de su propia área; poner criterios genéricos sin nombrar requisitos ni documentos UNSA; usar un único método insuficiente.
- **Ejercicio derivado:** `document_form` en **R4 02** (elaborar/completar el Programa anual de auditoría de la UNSA validando cobertura, priorización por riesgo e imparcialidad).

### 15. Informe de auditoría interna (`Apendice_2_Informe_de_auditoria_interna_ES.docx`)
- **Finalidad:** Comunicar formalmente los resultados ejecutados de una auditoría interna, incluyendo alcance, criterios, recomendaciones, recuento exacto de no conformidades y su enlace con medidas correctivas.
- **Secciones y campos (parafraseados):**
  1. *Metadatos ejecutados:* fecha del informe, período de la auditoría, quién la ejecutó, criterios aplicados, alcance auditado.
  2. *Seguimiento y mejora:* estado de seguimiento y recomendaciones de mejora.
  3. *Resultados:* cantidad total de no conformidades identificadas, más tabla detalle de no conformidades (descripción de cada NC y referencia cruzada al Formulario de acciones correctivas).
  4. *Firma del auditor líder / responsable.*
- **Adaptación 27701 / UNSA:** Se exige redacción de hallazgos basada en el estándar de auditoría (criterio + evidencia objetiva verificada + incumplimiento), separación respecto a observaciones/recomendaciones y referencia cruzada obligatoria hacia `pims-no-conformidades` (`NC-xx`).
- **Reglas implícitas:**
  - Consistencia matemática exacta: `total_nc == cantidad_de_filas_nc_detalladas`.
  - Toda NC listada debe tener referencia cruzada válida a una ficha de acción correctiva.
  - `fecha_informe >= fecha_fin_auditoria`.
  - Prohibido contar observaciones o recomendaciones como no conformidades (o viceversa).
- **Errores típicos:** Conteo total que no cuadra con la tabla; hallazgos sin evidencia objetiva («el personal parece poco capacitado»); olvidar la referencia cruzada al formulario de acción correctiva; fechar el informe antes de concluir el trabajo de campo.
- **Ejercicio derivado:** `document_form` en **R4 08** (redactar y validar el Informe de auditoría interna de la UNSA tras la simulación de auditoría).

### 16. Lista de apoyo para auditoría interna (`Apendice_3_Lista_de_apoyo_auditoria_interna_ES.docx`)
- **Finalidad:** Servir de lista de verificación en campo para comprobar sistemáticamente cada cláusula y control aplicable contra evidencia objetiva.
- **Secciones y columnas (parafraseadas):**
  1. *Cabecera y tabla de verificación (4 columnas):* cláusula/referencia normativa, pregunta de verificación, resultado de cumplimiento (`Sí/No` en la plantilla original) y evidencia observada. *(La plantilla incluye una tabla extensa para ISO 27001 y otra para continuidad ISO 22301; esta última se descarta para el PIMS.)*
- **Adaptación 27701 / UNSA:** En vez de copiar ~145 preguntas genéricas, la lista se **genera dinámicamente desde `pims_requirements`** (`clause_ref` como dato) y el estado real en BD (`in_force`, `unowned`, `draft`, `expired`, `missing`), reemplazando la columna binaria por el veredicto de auditoría (`conforme` / `observacion` / `no_conformidad`) y exigiendo asociar la **pregunta pertinente** y la **evidencia objetiva** a solicitar o constatada.
- **Reglas implícitas:**
  - Cada ítem enlaza a un requisito existente (`pims_requirements.clause_ref`).
  - Coherencia estricta evidencia → veredicto:
    - Documento vigente con responsable y fecha al día → `conforme`.
    - Documento vigente sin responsable asignado → `observacion`.
    - Documento en borrador, fecha de revisión vencida o inexistente → `no_conformidad`.
  - La evidencia solicitada debe corresponder al tipo de registro del requisito (no aceptar la Política como evidencia de evaluación de riesgos o de eficacia de capacitación).
- **Errores típicos:** Hacer preguntas cerradas sin relación con la cláusula; marcar «conforme» ante un borrador o un documento vencido; aceptar evidencia documental incorrecta o incompleta; emitir veredictos sin evidencia citada.
- **Ejercicio derivado:** **`audit_checklist`** (R4 04): lista generada desde `pims_requirements` y estado real de los documentos UNSA, donde el participante valida pregunta, evidencia a solicitar y veredicto.
