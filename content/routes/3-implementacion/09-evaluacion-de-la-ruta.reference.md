# Lista de comprobación final — Cadena de trazabilidad en Implementación (UNSA)

> Verifica antes de responder el examen la integridad de los 9 eslabones del PIMS:

1. **Brecha:** `missing > draft > expired > unowned > in_force`.
2. **RAT (`ORH`/`ORA`/`OBU`):** categorías sensibles disparan salvaguardas reforzadas (cifrado, mínimo privilegio, consentimiento).
3. **Riesgos:** `C + P`, datos sensibles fijan `C=2`, umbral `< 3`.
4. **SoA:** solo excluye por rol ausente o tipo de dato ausente, nunca por costo.
5. **Tratamiento:** referencia exclusivamente controles **aplicables en la SoA**; reduce `P` sin falsificar `C` ni incrementar el residual.
6. **Registros y NC:** contención inmediata ≠ acción correctiva sobre causa raíz + verificación tras lag temporal real.
7. **Monitoreo y Dirección (`9.1` → `9.3`):** auditoría interna + métricas alimentan las actas de Revisión por la Dirección.
