# Tasks 010 — Ruta 2 completa: Interpretación PIMS (Fase F9)

**Estado:** implementada (verificando `make verify`).

- [x] T1 Desarrollar Módulos `01-contexto-y-alcance` (`document_form` + `reference_doc: pims-alcance`) y `02-liderazgo-y-politica` (`document_form` + `reference_doc: pims-politica-privacidad`) (AC-010-1, 3)
- [x] T2 Desarrollar Módulos `03-riesgos-de-privacidad` (`risk_table` + sidecar) y `04-controles-y-aplicabilidad` (`soa_form` + sidecar) (AC-010-1, 4, 5)
- [x] T3 Desarrollar Módulos `05-controller-y-processor` (`branching` + sidecar), sidecar de `06-del-requisito-al-documento` y `07-competencia-monitoreo-mejora` (`competence_matrix` + `reference_doc: pims-competencia`) (AC-010-1, 2, 5, 6)
- [x] T4 Desarrollar Módulo `08-evaluacion-de-la-ruta` (`quiz` 10 preguntas, `final: true` + sidecar) verificando 960 min totales y 0 módulos `planned` en R2 (AC-010-1, 6)
- [x] T5 Verificar `seed/solutions.py` / `seed/demo.py` sobre R2 completa y actualizar `test_routes_2_4_content.py`, `test_routes_chain_api.py`, `test_analytics_api.py` + nuevos tests `@pytest.mark.ac("AC-010-...")` (AC-010-1..7)
- [x] T6 Añadir verificación E2E Playwright + `axe-core` sobre R2 `01-contexto-y-alcance`, actualizar `docs/demo.md` y pasar `make verify` completo (AC-010-7, 8)
