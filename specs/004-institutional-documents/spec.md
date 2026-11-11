# Spec 004 — Documentos institucionales versionados

**Estado:** aprobada (plan v2, Fase 3)

## Objetivo
Que la documentación interna ficticia de la UNSA (ROF, MOF, estatuto, cuadro de asignación de personal, reglamento) viva como **plantillas Markdown versionadas** y que cualquier modificación quede registrada —**qué cambió, quién, cuándo y por qué**— como un "git de incidencias": solicitud de cambio → revisión → nueva versión con diff.

## Historias
- **H1.** Como participante quiero leer los documentos vigentes y su historial para saber qué versión rige y cómo cambió.
- **H2.** Como participante quiero ver el diff entre dos versiones y clasificar su impacto (lo practicado en la Ruta 1).
- **H3.** Como participante quiero proponer una modificación con su justificación e impacto.
- **H4.** Como superadmin quiero aprobar o rechazar solicitudes, de modo que solo lo aprobado cree una versión nueva.
- **H5.** Como equipo quiero cargar los documentos iniciales (con historial de ejemplo) desde `content/institutional/`.

## Reglas de negocio
1. Un documento tiene versiones numeradas 1..N, **inmutables**; la vigente es la última. Cada versión guarda su contenido, hash SHA-256 del contenido normalizado, versión padre, autor, mensaje y fecha.
2. Normalización: saltos de línea `\r\n`→`\n`, espacios finales de línea eliminados, un único salto final. Un cambio que no altera el contenido normalizado **no es un cambio**.
3. Cualquier usuario autenticado puede **proponer** un cambio con `título`, `justificación`, `impacto` (`cosmetico | procedimental | estructural`) y el texto completo propuesto. La solicitud queda `open` y recuerda la versión base.
4. Solo el **superadmin** resuelve: `approve` o `reject` (con nota opcional). Resolver una solicitud ya resuelta es un error.
5. Aprobar crea la versión N+1 con el contenido propuesto (autor = quien propuso, mensaje = título), actualiza la vigente y marca la solicitud `approved`, todo de forma **atómica**. Si el documento avanzó desde la versión base (`stale_base`) no se puede aprobar; el superadmin puede rechazarla y quien propuso debe volver a proponer sobre la versión vigente.
6. Todo usuario autenticado puede leer documentos, versiones, diffs y solicitudes (transparencia).
7. Tipos de documento: `ROF`, `MOF`, `ESTATUTO`, `CUADRO_ASIGNACION`, `REGLAMENTO` (la Fase 4 añade los `PIMS_*`).

## Criterios de aceptación
### Lectura
- **AC-004-1** *Given* el seed, *When* `GET /documents`, *Then* 200 con 5 documentos (código, tipo, título, unidad responsable, versión vigente, fecha de la última versión, solicitudes abiertas); sin token → 401.
- **AC-004-2** *Given* un código, *When* `GET /documents/{code}`, *Then* 200 con metadatos y el contenido Markdown de la versión vigente; código inexistente → 404.
- **AC-004-3** *Given* un documento, *When* `GET /documents/{code}/versions`, *Then* lista ascendente con número, mensaje, autor, fecha y hash; `GET /documents/{code}/versions/{n}` devuelve el contenido; número inexistente → 404.
- **AC-004-4** *Given* dos versiones, *When* `GET /documents/{code}/diff?from=&to=`, *Then* devuelve hunks con líneas `add | del | ctx` (con numeración), y totales de adiciones/eliminaciones; si se omite `from` se usa `to-1`; sin cambios → hunks vacíos; versión inexistente → 404.

### Propuestas
- **AC-004-5** *Given* un usuario autenticado, *When* `POST /documents/{code}/change-requests` con datos válidos, *Then* 201, estado `open`, versión base = vigente, con proponente y fecha.
- **AC-004-6** *Given* datos inválidos (título o justificación vacíos, impacto desconocido, contenido > 200 000 caracteres), *Then* 422; *Given* contenido igual al vigente (tras normalizar, incluso con solo CRLF/espacios finales), *Then* 422.
- **AC-004-7** *Given* solicitudes, *When* `GET /change-requests?status=open` o `GET /documents/{code}/change-requests`, *Then* se listan con filtro; `GET /change-requests/{id}` incluye el diff base → propuesta; inexistente → 404.

### Resolución
- **AC-004-8** *Given* un `learner`, *When* resuelve una solicitud, *Then* 403; sin token → 401.
- **AC-004-9** *Given* el superadmin y una solicitud `open` cuya base es la vigente, *When* `approve`, *Then* 200, nueva versión N+1 (contenido propuesto, autor = proponente, mensaje = título, padre = N), documento actualizado, solicitud `approved` con quien resolvió, fecha y versión resultante; el diff N → N+1 coincide con el de la solicitud.
- **AC-004-10** *Given* que el documento avanzó desde la base, *When* `approve`, *Then* 409 con `code = "stale_base"` y la solicitud sigue `open`.
- **AC-004-11** *Given* una solicitud `open`, *When* `reject` (con nota), *Then* `rejected`, sin versión nueva; resolver otra vez → 409; `decision` distinta de approve/reject → 422.
- **AC-004-12** *Given* una versión, *Then* su `content_hash` es el SHA-256 del contenido normalizado y su cadena de padres es continua desde la versión 1 (que no tiene padre).

### Seed y contenido
- **AC-004-13** *Given* `content/institutional/`, *Then* hay 5 documentos válidos con historial: ROF 3 versiones, MOF 2, Reglamento 2, Estatuto 1, Cuadro 1; los códigos de unidad responsable existen en el seed de la universidad.
- **AC-004-14** *Given* el seed, *When* se ejecuta dos veces, *Then* no duplica documentos ni versiones y **no pisa** lo creado desde la app; con `--reset-documents` se restaura el contenido inicial.

### Transversales
- **AC-004-15** La API expone los paths/métodos de `contracts/openapi.yaml`.
- **AC-004-16** `documents` cumple AC-001-5 (sin frameworks en `domain`/`application`).
- **AC-004-17** *Given* la UI, *Then*: `/documents` lista los documentos y solicitudes abiertas; el detalle muestra contenido, historial y solicitudes; el diff se ve con líneas añadidas/eliminadas diferenciadas (no solo por color); cualquier usuario puede proponer; solo el superadmin ve los botones aprobar/rechazar; los diffs del módulo 5 de la Ruta 1 se muestran con el mismo estilo.

## Fuera de alcance
Edición colaborativa en vivo, comentarios por línea, fusión (*merge*) de solicitudes en conflicto, exportar a `.md`, plantillas PIMS (Fase 4), notificaciones.

## Contenido inicial (ficticio)
| Código | Tipo | Versiones | Responsable |
|---|---|---|---|
| `rof` | ROF | 3 (v2: errata «prescide»→«preside»; v3: añade al Oficial de Protección de Datos en TI) | SGEN |
| `mof` | MOF | 2 (v2: crea el cargo de Oficial de Protección de Datos Personales) | ORH |
| `estatuto` | ESTATUTO | 1 | SGEN |
| `cuadro-asignacion` | CUADRO_ASIGNACION | 1 | ORH |
| `reglamento-evaluacion` | REGLAMENTO | 2 (v2: plazo de entrega de actas de 10 a 5 días) | ORA |
