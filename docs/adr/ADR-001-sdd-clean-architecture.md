# ADR-001 — Spec-Driven Development + Clean Architecture

- **Estado:** aceptada
- **Fecha:** 2026-11-11

## Contexto
El POC debe ser trazable (requisitos → tests → código) y fácil de evolucionar, con un backend que pueda cambiar adaptadores (BD, IA) sin tocar reglas de negocio.

## Decisión
- **SDD:** cada fase tiene `specs/NNN-*/{spec,plan,tasks}.md`. Los criterios de aceptación `AC-NNN-x` (Given/When/Then) se convierten en tests marcados con `@pytest.mark.ac("AC-NNN-x")`. El contrato OpenAPI se escribe antes de implementar.
- **Clean Architecture** por módulo: `domain ← application ← infrastructure / interface`. Puertos en `application`, adaptadores en `infrastructure`, composición solo en `main.py`.
- Se hace cumplir con un test de arquitectura (`tests/unit/test_architecture.py`, AC-001-5).

## Consecuencias
+ Reglas críticas testeables sin BD ni HTTP. Cambiar `agy` por otra IA = nuevo adaptador.
− Más archivos/boilerplate por caso de uso; se acepta por el valor didáctico y de mantenimiento.
