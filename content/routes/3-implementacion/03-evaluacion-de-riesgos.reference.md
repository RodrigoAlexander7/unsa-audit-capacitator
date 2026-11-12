# Cuadro modelo — Fila resuelta de evaluación de riesgos (UNSA)

> Modelo adaptado para un activo no incluido en tu práctica (para demostrar trazabilidad completa).

- **Activo:** Sistema de Planillas y RR. HH. (`ORH`)
- **Categorías:** identificación, datos laborales, datos bancarios, **datos de salud**
- **Controles existentes:** cifrado de sesión y copias diarias, pero permisos amplios dentro del módulo de abonos
- **Amenaza:** extracción masiva de cuentas bancarias o descansos médicos
- **Vulnerabilidad:** ausencia de mínimo privilegio por perfiles dentro del módulo de pagos
- **Propietario del riesgo:** Jefe de la Oficina de Recursos Humanos (`jefe-orh`)
- **Valoración:** Consecuencia **`2`** (contiene salud/bancarios) + Probabilidad **`1`** (controles parciales) = **Nivel `3` → No aceptable (umbral `< 3`)** → pasa a Plan de tratamiento.
