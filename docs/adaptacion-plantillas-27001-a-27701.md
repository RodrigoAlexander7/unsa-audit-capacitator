# Adaptación de las plantillas ISO 27001 (`raw/files`) a ISO 27701

> Nota de trabajo para las Fases 4 (set documental PIMS), 5 (Ruta 3 y Ruta 4) y 6 (analytics).

## Qué son y cómo se usarán
`raw/files/` contiene 12 plantillas de un toolkit comercial de ISO/IEC 27001 (edición 2013: cláusulas 4–10 y Anexo A con numeración `A.x.y.z`), 10 `.docx` y 2 `.xlsx`. Son **material de terceros** (la plantilla acredita a su autor):

- **No se copian textos ni se versiona `raw/`** (está en `.gitignore`). Se usan como *referencia estructural*: qué secciones tiene cada documento, qué registros exige y qué mecánica práctica enseñan.
- Todo el contenido que entra al repo se **redacta de nuevo**, en español, adaptado a ISO/IEC 27701 (privacidad: datos personales, roles *controller/processor*, derechos de los titulares) y a la UNSA ficticia.
- Las cláusulas se guardan como **dato** (`pims_requirements.clause_ref`), porque la numeración depende de la edición (2019 vs 2025).

## Mapeo plantilla → documento PIMS → uso en la capacitación

| Plantilla de origen | Documento PIMS (§5 del PLAN) | Adaptación a 27701 / UNSA | Ruta / ejercicio |
|---|---|---|---|
| *(sin plantilla)* | 1. Alcance del PIMS (4.3) | Fronteras: unidades, sistemas y actividades de tratamiento de la UNSA ficticia; roles controller/processor | R3: redactar el alcance eligiendo unidades y sistemas de la BD |
| *(sin plantilla)* | 2. Política de privacidad (5.2) | Principios, derechos de titulares, responsables | R2: identificar elementos obligatorios; R3: completar |
| **Metodología de evaluación y tratamiento de riesgos** | 3. Proceso de evaluación de riesgos de privacidad (6.1.2) | Activos → amenazas → vulnerabilidades → consecuencia (0–2) + probabilidad (0–2) = riesgo; ≥ 3 no aceptable. Añadir **impacto sobre los titulares** y categorías sensibles | R3: `risk_rating` |
| **Cuadro de evaluación de riesgos** (xlsx, hojas Categorías/Amenazas/Vulnerabilidades) | 7. Resultados de la evaluación (8.2) | Activos = sistemas y actividades de tratamiento del seed; catálogos propios de amenazas y vulnerabilidades | R3: tabla de riesgos generada desde la BD |
| **Cuadro de tratamiento de riesgos** (xlsx, hojas Opciones/Controles) | 8. Resultados del tratamiento (8.3) y 5. Plan de tratamiento (6.1.3 f) | 4 opciones (controles, transferir, evitar, aceptar) + riesgo residual; controles de privacidad para controller y processor (redactados por nosotros) | R3: `treatment_choice` |
| *(derivado de la metodología + cuadro de tratamiento)* | 4. Declaración de aplicabilidad (6.1.3 e) | Aplica / no aplica + justificación + documento de respaldo | R3 (módulo demo): `soa_form` |
| **Informe sobre evaluación y tratamiento** | 7 y 8 (informe consolidado) | Resumen del proceso: objetivo, alcance, periodo, participantes, metodología, documentos | R3: completar informe |
| *(sin plantilla directa)* | 6. Programa de seguridad documentado, con gestión de incidentes (6.1.3 c) | Incluye plan de respuesta a **brechas de datos personales** | R3 |
| **Plan de capacitación y concienciación** | 9. Evidencia de competencia (7.2) | Matriz cargo → competencia → capacitación → evidencia; enlaza con las 4 rutas de esta plataforma | R3: `competence_matrix`; analytics F6 |
| *(sin plantilla directa)* | 10. Evidencia de monitoreo y medición (9.1) | Indicadores de privacidad (p. ej. solicitudes de titulares atendidas en plazo) | R4: revisar evidencia |
| **Procedimiento y formulario de medidas correctivas** | 11. No conformidades y acciones correctivas (10.2) | Corrección vs acción correctiva; causa raíz; verificación de eficacia | R3/R4: `nonconformity_form` |
| **Minutas de revisión por la dirección** | *(opcional, 9.3)* | Se propone como documento 12 del set; no figura en la lista original | R3 |
| **Procedimiento de auditoría interna**, **Programa anual**, **Informe de auditoría** | Ruta 4 (ISO 19011) | Reescritos para auditores internos de la UNSA: criterios, alcance, método, hallazgos | R4: plan y informe de auditoría |
| **Lista de apoyo de auditoría interna** (cláusula + pregunta + cumple + evidencia) | Ruta 4: lista de verificación | Se **genera desde `pims_requirements`** (una pregunta por documento/cláusula) en vez de copiar las preguntas | R4: `audit_checklist` |

## Ejercicios de la Ruta 3 que se derivan de este material
1. **`risk_rating`**: dados un activo y un escenario (amenaza + vulnerabilidad) de la UNSA, el participante valora consecuencia y probabilidad (0–2); el backend calcula el riesgo, lo compara con el rango esperado y explica la desviación. Los activos salen de `systems`/`processing_activities` y las categorías sensibles (salud, socioeconómicos) elevan la consecuencia.
2. **`treatment_choice`**: para riesgos no aceptables, elegir la opción de tratamiento y los controles; el backend verifica coherencia (p. ej. "aceptar" solo si el costo del control supera el impacto) y calcula el riesgo residual esperado.
3. **`soa_form`**: completar la declaración de aplicabilidad de una oficina (aplica/no, justificación, documento de respaldo); validación automática y coherencia con el plan de tratamiento.
4. **`competence_matrix`**: asignar a cada cargo la capacitación necesaria según su rol (controller, processor, DPO…).
5. **`nonconformity_form`**: distinguir corrección de acción correctiva, redactar la causa y definir la verificación de eficacia.

## Qué NO se hará
- Copiar párrafos, tablas ni catálogos de las plantillas.
- Reproducir el texto o los títulos de los controles del Anexo A de la norma (se parafrasean y se identifican por tema).
- Versionar `raw/` (binarios de terceros). Si se desea compartirlo con el equipo, usar un repositorio privado o un almacenamiento aparte.

## Pendientes de verificación
- Confirmar con quien conserve la licencia del toolkit si se permite derivar material de capacitación. Mientras tanto, todo el contenido es propio.
- Definir el catálogo propio de amenazas/vulnerabilidades de la UNSA (≈ 15 de cada una, enfocadas en datos personales) al abordar la Fase 5.
