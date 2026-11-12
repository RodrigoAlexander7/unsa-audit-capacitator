---
title: Controller y processor
minutes: 120
---

# Controller y processor

> Material formativo para este POC (datos 100 % ficticios de la UNSA). Las referencias a cláusulas se tratan como dato parametrizable según la edición vigente.

Uno de los conceptos centrales de ISO/IEC 27701 es que las obligaciones de privacidad cambian según el papel de quien trata los datos:

- **Responsable del tratamiento (*Controller*):** determina **por qué** (finalidad) y **cómo** (medios esenciales) se tratan los datos personales. La UNSA es responsable de sus procesos académicos, laborales y de bienestar estudiantil.
- **Encargado del tratamiento (*Processor*):** trata datos personales **únicamente por cuenta y bajo instrucciones documentadas** de un responsable (por ejemplo, el proveedor de respaldos en la nube contratado por la UNSA o el laboratorio clínico externo para `OBU`/`FCSA`).

## Reglas prácticas que verifica un auditor

1. **Soporte interno (`OTI`) vs. encargado externo:** dentro de la universidad, `OTI` administra infraestructura y actúa como custodio operativo para `ORA` u `ORH`, pero frente al ciudadano la **UNSA sigue siendo un único responsable**. En cambio, un proveedor independiente contratado exige un **contrato de encargo**.
2. **Límite absoluto a fines propios:** un encargado **no puede** reutilizar los datos del responsable para analítica comercial, entrenamiento propio ni cesión a subencargados sin autorización escrita.
3. **Asistencia y término del contrato:** si un titular envía una solicitud ARCO al encargado, este **no responde por cuenta propia**: asiste y traslada al responsable (`DPO` de la UNSA). Al finalizar el vínculo, devuelve o destruye los datos de forma verificable.

## Ejemplo resuelto y práctica

Revisa a la izquierda la ficha modelo de relación Responsable ↔ Encargado para el respaldo en nube de la UNSA y decide qué corresponde hacer en cuatro casos operativos.
