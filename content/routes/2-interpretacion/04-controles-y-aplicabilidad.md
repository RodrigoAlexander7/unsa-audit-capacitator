---
title: Controles y declaración de aplicabilidad
minutes: 140
---

# Controles y declaración de aplicabilidad

> Material formativo para este POC (datos 100 % ficticios de la UNSA). Las referencias a cláusulas se tratan como dato parametrizable según la edición vigente.

La **Declaración de Aplicabilidad (SoA)** explica con transparencia qué controles de seguridad y de privacidad adopta la universidad y **por qué descarta los que no corresponden**. En ISO/IEC 27701, ese análisis cambia según el rol que desempeña la entidad en cada tratamiento.

## Criterios para decidir la aplicabilidad

1. **Cuándo SÍ aplica un control:**
   - Se necesita para reducir riesgos identificados como no aceptables (`>= 3`).
   - Responde a una obligación legal o estatutaria (p. ej. consentimiento expreso para datos sensibles, atención de derechos de titulares o notificación de brechas).
   - Se deriva de la relación contractual con terceros (p. ej. contratos con encargados que procesan datos por cuenta de la UNSA).
2. **Cuándo NO aplica legítimamente un control:**
   - **Rol de responsable vs. encargado:** si una oficina únicamente actúa como **responsable (`controller`)** y no presta servicios de tratamiento para terceros clientes, los controles exclusivos del **encargado (`processor`)** (seguir instrucciones de un cliente externo, asistirlo frente a sus titulares) **no aplican** por ausencia del rol.
   - **Naturaleza de los datos o flujo:** si una unidad (como `BIBL`) no recopila ni trata datos de salud, los controles específicos para categorías médicas no aplican en ese ámbito.
3. **Justificación prohibida ante auditoría:** nunca se excluye un control necesario alegando «alto costo», «falta de personal» o «incomodidad técnica».

## Ejemplo resuelto y práctica

Consulta en el panel lateral el criterio comparativo aplicado a la `BIBL` y resuelve la aplicabilidad de controles para la **Oficina de Bienestar Universitario (`OBU`)**.
