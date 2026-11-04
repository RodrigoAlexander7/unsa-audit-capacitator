# Spec 006 — Rutas 2–4 y evaluación controller/processor

**Estado:** aprobada (plan v2, Fase 5)

## Objetivo
1. Dar **estructura completa** a las Rutas 2 (16 h), 3 (24 h) y 4 (32 h) —todos sus módulos listados— con **un módulo demo interactivo cada una** que sea jugable y corrija en el backend, de modo que la cadena R1 → R2 → R3 → R4 funcione de punta a punta con sus prerrequisitos.
2. Añadir el **módulo de evaluación** para los roles **controller** y **processor**, con resultados por competencia y por requisito del PIMS.

## Historias
- **H1.** Como participante quiero ver todos los módulos previstos de cada ruta aunque aún no estén desarrollados.
- **H2.** Como participante de Interpretación quiero relacionar preguntas de un auditor con el documento del PIMS que las responde.
- **H3.** Como participante de Implementación quiero completar la declaración de aplicabilidad de una oficina (aplica / no aplica + justificación).
- **H4.** Como participante de Auditor quiero auditar el conjunto PIMS real de la UNSA y clasificar mis hallazgos.
- **H5.** Como controller o processor quiero evaluar mis conocimientos y saber qué competencias y requisitos debo reforzar.

## Reglas de negocio
### Rutas
1. Un módulo `planned` está listado pero **no es accesible**, es no obligatorio y no tiene ejercicio. No cuenta en `modules_total` (se informa aparte como `modules_planned`). Una ruta solo se completa si tiene al menos un módulo **publicado** y todos los obligatorios están completados.
2. Cada una de las Rutas 2–4 tiene **un único módulo obligatorio** (el demo); aprobarlo completa la ruta. Las horas acreditadas son las del módulo demo (R2 2 h, R3 3 h, R4 4 h): el POC desarrolla solo una parte de las horas previstas y la UI lo indica.
3. Nuevo tipo de ejercicio `soa_form`: por cada control, el participante decide *aplica / no aplica* y elige una justificación. Puntaje = mitad por acertar la aplicabilidad y mitad por la justificación, promediado.
4. Nuevo generador `pims_audit_findings`: construye, desde el estado real del conjunto PIMS (Fase 4), una clasificación requisito → hallazgo (`conforme` / `observacion` / `no_conformidad`): vigente → conforme; vigente sin responsable → observación; borrador, vencido o inexistente → no conformidad.
5. El demo de Interpretación es un `matching` estático: pregunta de un auditor → requisito PIMS (los ids son códigos de requisito y deben existir).
### Evaluación
6. Perfiles: `controller` y `processor`; 12 preguntas por perfil. Cada pregunta tiene una **competencia** y un **requisito PIMS** (código) asociados, ambos datos de contenido.
7. Se inicia una evaluación (se fija el orden de preguntas) y se envía **una sola vez**; se puede repetir iniciando otra. Aprueba con ≥ 70 %.
8. El resultado incluye puntaje, aprobado, puntaje por competencia, puntaje por requisito/cláusula y la corrección de cada pregunta con su explicación. Solo el dueño ve sus intentos.

## Criterios de aceptación
### Rutas
- **AC-006-1** *Given* `content/routes`, *Then* R2, R3 y R4 tienen 8, 9 y 10 módulos cuyos minutos suman 960, 1440 y 1920; cada una con exactamente un módulo publicado y obligatorio (con ejercicio) y los demás `planned`.
- **AC-006-2** *Given* un módulo `planned`, *When* se consulta o se intenta resolver, *Then* 409; en el detalle de ruta aparece con `planned = true` y estado `locked`; `modules_total` no lo cuenta y `modules_planned` sí.
- **AC-006-3** *Given* un participante, *When* intenta matricularse en R3 sin haber aprobado R2, *Then* 409 `prerequisite_not_met`; tras aprobar R1, R2 y R3 se habilita R4 y completar las cuatro acredita 12 + 2 + 3 + 4 = 21 h.
- **AC-006-4** *Given* el demo de R2, *Then* es un `matching` válido cuyas respuestas y opciones corresponden a requisitos de `pims/requirements.yaml`; la respuesta perfecta da 100.
- **AC-006-5** *Given* `soa_form`, *Then* la versión pública no incluye `applies`, `reason` ni explicaciones; el puntaje otorga medio punto por aplicabilidad y medio por justificación; respuestas con forma inválida → 422.
- **AC-006-6** *Given* el demo de R3 (SoA de la Oficina de Registros Académicos), *Then* es resoluble con 100 y da crédito parcial a respuestas parcialmente correctas.
- **AC-006-7** *Given* el generador `pims_audit_findings`, *Then* refleja el estado real del conjunto PIMS según las reglas del punto 4 y cambia si cambia el estado (documento/fecha); la respuesta derivada da 100.
- **AC-006-8** *Given* la aprobación del único módulo obligatorio, *Then* la matrícula pasa a `completed` y se habilita la ruta siguiente.
### Evaluación
- **AC-006-9** *Given* `content/assessment`, *Then* hay 2 perfiles × 12 preguntas con ids únicos, opciones válidas, al menos 5 competencias por perfil y cada pregunta asociada a un requisito PIMS existente; ambos perfiles cubren brechas; el de controller cubre contratos con encargados y el de processor instrucciones documentadas y subencargados.
- **AC-006-10** *Given* un usuario autenticado, *When* `POST /assessments {profile}`, *Then* 201 con las 12 preguntas públicas (sin respuesta correcta ni explicación) en un orden determinista por intento; perfil inválido → 422; sin token → 401.
- **AC-006-11** *Given* un intento en curso, *When* `POST /assessments/{id}/submit`, *Then* devuelve puntaje, `passed` (≥ 70), puntaje por competencia y por requisito (aciertos/total/%) y la corrección por pregunta; enviar otra vez → 409; el intento de otra persona → 404.
- **AC-006-12** *Given* intentos previos, *When* `GET /assessments`, *Then* lista los míos (perfil, estado, puntaje, fechas), más recientes primero; `GET /assessments/{id}` de uno finalizado devuelve su resultado.
- **AC-006-13** Preguntas sin responder o con ids desconocidos cuentan como incorrectas; `answers` con forma inválida → 422.
### Transversales
- **AC-006-14** La API expone los paths/métodos de `contracts/openapi.yaml`.
- **AC-006-15** `assessment` cumple AC-001-5 (sin frameworks en `domain`/`application`).
- **AC-006-16** *Given* la UI, *Then*: las rutas muestran los módulos en preparación como "Próximamente"; el ejercicio `soa_form` se resuelve y se corrige; `/assessment` permite elegir perfil, responder y ver resultados por competencia y requisito con enlaces al conjunto PIMS.

## Fuera de alcance
Desarrollar el resto de módulos de las Rutas 2–4, bancos de preguntas ampliables desde la UI, límites de intentos o tiempo, certificados, analytics (F6).

## Módulos demo
| Ruta | Módulo demo | Ejercicio | Min | Obligatorio |
|---|---|---|---|---|
| R2 Interpretación | Del requisito al documento | `matching` estático (pregunta del auditor → requisito) | 120 | sí |
| R3 Implementación | Declaración de aplicabilidad de una oficina | `soa_form` (8 controles) | 180 | sí |
| R4 Auditor | Simulación: auditar el PIMS de la UNSA | `matching` generado `pims_audit_findings` | 240 | sí |
