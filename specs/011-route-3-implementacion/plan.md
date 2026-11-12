# Plan 011 — Ruta 3 completa: Implementación PIMS (Fase F10)

**Estado:** en ejecución.

## Diseño de los 9 módulos (`content/routes/3-implementacion/`)

| Orden | Slug | Min | Tipo ejercicio | Ejemplo resuelto | Enfoque implementador |
|---|---|---:|---|---|---|
| 1 | `01-analisis-de-brecha` | 150 | `document_form` | `01-analisis-de-brecha.reference.md` | Priorización de brechas reales UNSA (`missing`, `draft`, `expired`, `unowned`) |
| 2 | `02-inventario-de-activos-y-tratamientos` | 180 | `document_form` | `02-inventario-de-activos-y-tratamientos.reference.md` | Registro de Actividades de Tratamiento (RAT) de `ORH` + regla `requires_if` |
| 3 | `03-evaluacion-de-riesgos` | 200 | `risk_table` | `03-evaluacion-de-riesgos.reference.md` | Valoración completa de 5 sistemas UNSA + selección de vulnerabilidad/dueño |
| 4 | `04-declaracion-de-aplicabilidad` | 180 | `soa_form` (preservado) | `04-declaracion-de-aplicabilidad.reference.md` | SoA de `ORA` frente al ejemplo resuelto de `Biblioteca Central` |
| 5 | `05-politicas-y-procedimientos` | 180 | `document_form` | `reference_doc: pims-programa-seguridad` | Procedimiento de gestión de brechas e incidentes (`OTI` / `CISO` / `DPO`) |
| 6 | `06-plan-de-tratamiento-y-recursos` | 200 | `treatment_table` | `06-plan-de-tratamiento-y-recursos.reference.md` | Plan de tratamiento enlazado a SoA, dueño, plazo y riesgo residual |
| 7 | `07-evidencias-y-registros` | 150 | `nonconformity_form` | `07-evidencias-y-registros.reference.md` | Corrección vs. acción correctiva sobre evidencias de respaldos y consentimientos |
| 8 | `08-indicadores` | 100 | `document_form` | `08-indicadores.reference.md` | Diseño de `pims-monitoreo` + acta de revisión por la dirección (`disjoint`, `date_order`) |
| 9 | `09-evaluacion-de-la-ruta` | 100 | `quiz` (`final: true`) | `09-evaluacion-de-la-ruta.reference.md` | Evaluación integradora de implementación PIMS (10 ítems) |

Total: `150 + 180 + 200 + 180 + 180 + 200 + 150 + 100 + 100 = 1440` min (`24 h`).
