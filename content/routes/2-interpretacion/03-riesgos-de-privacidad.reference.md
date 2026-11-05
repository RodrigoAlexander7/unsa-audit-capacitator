# Metodología aplicada — Ejemplos resueltos (UNSA)

> Referencia didáctica del ciclo de interpretación sobre la metodología UNSA (`C + P`, umbral `< 3`).

| Activo UNSA | Categorías | Controles observados | C | P | Nivel | Resultado | Criterio aplicado |
|---|---|---|---:|---:|---:|---|---|
| **Sistema de Matrícula (`ORA`)** | Identificación, datos académicos (no sensible) | Cifrado en tránsito, rol único, sin control formal de cambios en base de datos | 2 | 1 | 3 | **No aceptable** | Alterar matrículas afecta el vínculo académico oficial; control parcial sitúa P=1 |
| **Trámite Documentario (`SGEN`)** | Identificación, expedientes administrativos (no sensible) | Archivo físico con llave y registro de acceso, sin inventario automatizado | 1 | 1 | 2 | **Aceptable** | Impacto moderado (1) y controles razonables (1); nivel 2 por debajo del umbral `3` |

**Lección clave:** si el sistema involucra **datos de salud** u otras categorías sensibles, la consecuencia siempre toma el valor **`2`**, aunque existan controles técnicos básicos.
