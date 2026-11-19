---
title: Análisis de brecha
minutes: 150
---

# Análisis de brecha

> Material formativo para este POC (datos 100 % ficticios de la UNSA). Las referencias a cláusulas se tratan como dato parametrizable según la edición vigente.

Implementar un PIMS no empieza creando carpetas desde cero, sino **contrastando lo que la institución ya opera** contra los requisitos documentales y de control exigidos, identificando brechas por severidad de estado (**inexistente > borrador > vencido > sin responsable > vigente**) y planificando cierres ordenados.

## Regla de precedencia en el diagnóstico UNSA

1. **Inexistente (`missing`):** ausencia total del requisito (como `pims-monitoreo`). No permite evaluar si el sistema funciona y genera no conformidad directa.
2. **Borrador (`draft`):** existe un texto preliminar sin aprobación formal (`pims-soa`, `pims-resultados-tratamiento`). Carece de autoridad vinculante frente a auditoría.
3. **Vencido (`expired`):** documento aprobado cuya revisión expiró (`pims-proceso-riesgos`, `pims-no-conformidades`), perdiendo vigencia frente a cambios recientes de sistemas o riesgos.
4. **Sin responsable (`unowned`):** carece de cargo o unidad dueña que responda por su mantenimiento y cumplimiento (`pims-plan-tratamiento`).

## Ejemplo resuelto y práctica

Consulta en el panel lateral el análisis de brecha modelo para una oficina académica y elabora el **Diagnóstico de Brecha del Conjunto PIMS de la UNSA**.
