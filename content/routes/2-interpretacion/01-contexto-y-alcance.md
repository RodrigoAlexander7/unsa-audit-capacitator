---
title: Contexto de la organización y alcance del PIMS
minutes: 120
reference_doc: pims-alcance
---

# Contexto de la organización y alcance del PIMS

> Material formativo para este POC (datos 100 % ficticios de la UNSA). Las referencias a cláusulas se tratan como dato parametrizable según la edición vigente.

Antes de seleccionar controles o redactar políticas, la universidad debe comprender **qué factores internos y externos condicionan su tratamiento de datos personales**, qué exigen sus **partes interesadas** (estudiantes, docentes, personal administrativo, entes reguladores y proveedores) y **hasta dónde llega exactamente el PIMS**.

## Qué decide un implementador y qué verifica un auditor

1. **Coherencia organizativa y tecnológica (`UNSA`):** incluir una unidad (por ejemplo, `OBU` o `ORA`) obliga a incluir los sistemas de información y actividades con los que trata datos personales, además de `OTI` cuando opera la infraestructura compartida.
2. **Fronteras y encargados en el perímetro:** excluir una facultad, un sistema o un proceso requiere una **justificación verificable** (por ejemplo, implantación por etapas o datos verdaderamente anonimizados) y documentar cómo se controlan las **interfaces o transferencias** hacia fuera del alcance. Nunca es válido excluir un tratamiento activo «por ahorrar costos».
3. **Rol controller vs. processor dentro del alcance:** la UNSA decide finalidades y medios sobre los datos académicos, laborales y de salud estudiantil (responsable), mientras proveedores externos —como alojamiento en la nube o laboratorios médicos— actúan bajo contrato como encargados.
4. **Segregación y vigencia:** quien diseña y mantiene el documento técnico (p. ej. el Oficial de Protección de Datos Personales o el Jefe de la `OTI`) **no lo autoaprueba** como máxima autoridad; la aprobación recae en la Alta Dirección (`Rector`) y la revisión es al menos anual.

## Ejemplo resuelto de la UNSA

En el panel lateral («Ejemplo resuelto (UNSA)») tienes el **Alcance del PIMS vigente** de la universidad (`pims-alcance`), con sus procesos, sistemas, unidades incluidas, exclusiones iniciales y criterios de revisión.

## Tu práctica

La UNSA prepara la **segunda etapa** de su Alcance para incorporar la **Oficina de Bienestar Universitario (`OBU`)** y las prácticas clínicas de la **Facultad de Ciencias de la Salud (`FCSA`)**. Completa la ficha de revisión validando responsables, fechas, unidades, sistemas en alcance y justificaciones defendibles ante auditoría.
