# Tasks 005 — Conjunto documental del PIMS

- [x] T1 Contrato `contracts/openapi.yaml` (AC-005-9)
- [x] T2 domain: `DocumentKind` PIMS_*, `DocumentLifecycle`, campos nuevos, `pims.py` + unit tests (AC-005-2, 4)
- [x] T3 application: puertos, casos de uso + unit tests (AC-005-1, 3)
- [x] T4 infrastructure: ORM, migración 0005 (subir y `alembic check` sin diferencias), repositorio, loaders (AC-005-6, 7)
- [x] T5 Contenido: `content/pims/requirements.yaml` + 10 documentos PIMS (AC-005-6, 7)
- [x] T6 interface: `/pims/*` y campos nuevos en `/documents`; wiring (AC-005-1, 3, 5)
- [x] T7 seed: `sync_pims_requirements` (AC-005-6)
- [x] T8 tests de integración (AC-005-1, 3, 5, 6, 8, 9)
- [x] T9 Frontend: `/documents/pims`, estados en `/documents` y en el detalle (AC-005-11)
- [x] T10 Verificación completa, docs y commit único de la fase (AC-005-10)

## Notas de cierre
- Verificado: ruff, pyright, **192 tests backend** (129 unit + 63 integración con Postgres real), svelte-check, 17 vitest y build.
- AC-005-11 verificado en el navegador integrado: resumen «5 de 11 vigentes (45 %)», contadores por estado, matriz con las 11 filas en el orden esperado, enlaces a cada documento, «No existe» para 9.1 y la SoA mostrada como borrador. Pendiente de ver a mano: el despliegue «¿Qué se espera?» en pantalla (existe en el HTML).
- **Contenido original:** los 10 documentos y `requirements.yaml` se redactaron de nuevo usando las 4 plantillas nuevas (alcance, política, SoA, plan de tratamiento) y las 12 anteriores solo como guía de estructura (ver `docs/adaptacion-plantillas-27001-a-27701.md`). La SoA usa 15 temas de control propios en lugar del Anexo A.
- **Hallazgos sembrados para la Ruta 4** (además del CAP sin el cargo de DPO de la F3): proceso de riesgos y registro de no conformidades vencidos; SoA y resultados del tratamiento en borrador (con un riesgo residual de nivel 3 sin tratar y un riesgo sin opción elegida); plan de tratamiento sin responsable y con una actividad sin dueño; matriz de competencia con tres cargos sin registro (incluido el Oficial de Protección de Datos); NC-03 sin acción correctiva asignada; no existe evidencia de monitoreo y medición.
- Las fechas de revisión de los vigentes están en 2030 y las de los vencidos en 2025 para que el reparto sembrado no dependa del reloj; un test fija `today` y verifica cómo cambia el estado con el tiempo (con fecha 2031 todo lo vigente vence).
- El plan de tratamiento tiene una columna "Control (SoA)" que referencia el número de fila de la SoA; es la base del ejercicio de coherencia `soa_form` ↔ plan de la Fase 5.
- Pendiente para fases siguientes: publicar un borrador desde la UI, ejercicios de las Rutas 2–4 sobre este conjunto (F5), analytics por cláusula (F6).
