# Contenido (fuente de verdad)

Todo el contenido es **ficticio** (POC) y parafraseado. El backend lo sincroniza a PostgreSQL con `uv run python -m unsa_audit.seed`.

```
routes/<n>-<codigo>/
├── route.yaml                  code, order, title, description, hours, prerequisite
├── NN-slug.md                  frontmatter (title, minutes, mandatory, final) + lección en Markdown
└── NN-slug.exercise.json       kind, pass_score, y spec  |  generator + params
```

```
institutional/<codigo>/
├── document.yaml               code (= nombre de la carpeta), kind, title, owner_unit (código de unidad,
│                               opcional), lifecycle (in_force | draft), review_date (opcional)
└── vN.md                       v1.md … vN.md contiguas; frontmatter (message, author, date) + Markdown

pims/requirements.yaml          los 11 requisitos documentales del PIMS (en orden): code, clause_ref,
                                title, document_kind, summary, expected_evidence, responsible_unit
```

La versión vigente de un documento es la mayor `vN`. Tipos (`kind`): `ROF`, `MOF`, `ESTATUTO`, `CUADRO_ASIGNACION`, `REGLAMENTO` y los 11 `PIMS_*` (un documento como máximo por tipo PIMS; el de monitoreo y medición falta a propósito). Los documentos `pims-*` son ficticios y se redactaron de nuevo, no se copian de plantillas de terceros.

Tipos de ejercicio: `ordering`, `matching`, `single_choice`, `quiz`, `branching`.
Generadores (desde la BD ficticia): `org_levels`, `responsibility_cases`, `system_owners`.

Reglas: los ids de las soluciones deben existir (se valida al cargar y en los tests); los minutos de una ruta
con contenido deben sumar `hours * 60`.
