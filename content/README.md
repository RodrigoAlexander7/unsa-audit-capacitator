# Contenido (fuente de verdad)

Todo el contenido es **ficticio** (POC) y parafraseado. El backend lo sincroniza a PostgreSQL con `uv run python -m unsa_audit.seed`.

```
routes/<n>-<codigo>/
├── route.yaml                  code, order, title, description, hours, prerequisite
├── NN-slug.md                  frontmatter (title, minutes, mandatory, final) + lección en Markdown
└── NN-slug.exercise.json       kind, pass_score, y spec  |  generator + params
```

Tipos de ejercicio: `ordering`, `matching`, `single_choice`, `quiz`, `branching`.
Generadores (desde la BD ficticia): `org_levels`, `responsibility_cases`, `system_owners`.

Reglas: los ids de las soluciones deben existir (se valida al cargar y en los tests); los minutos de una ruta
con contenido deben sumar `hours * 60`.
