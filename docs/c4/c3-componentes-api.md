# C4 — Nivel 3: Componentes del API

```mermaid
C4Component
  title C3 - Componentes de la API (por módulo, Clean Architecture)
  Container_Boundary(api, "API FastAPI") {
    Component(main, "Composition root", "main.py", "Conecta puertos con adaptadores")
    Component(iface, "Interface layer", "FastAPI routers + schemas", "HTTP, validación, DTOs")
    Component(app, "Application layer", "Casos de uso + puertos", "CheckHealth (F0); EnrollInRoute, CompleteExercise, SubmitAssessment, ProposeDocChange, AskAdvisor (fases siguientes)")
    Component(dom, "Domain layer", "Entidades, VO, reglas", "Route, Module, Enrollment, Document, Version, PimsRequirement (fases siguientes)")
    Component(infra, "Infrastructure layer", "SQLAlchemy, JWT, ContentLoader, AgyCliAdapter", "Implementa puertos")
  }
  ContainerDb(db, "PostgreSQL")
  System_Ext(agy, "agy CLI")
  Rel(main, iface, "monta routers")
  Rel(iface, app, "invoca")
  Rel(app, dom, "usa")
  Rel(infra, app, "implementa puertos de")
  Rel(infra, db, "lee/escribe")
  Rel(infra, agy, "subprocess")
```

Regla: `domain` y `application` no importan frameworks de I/O (verificado por `tests/unit/test_architecture.py`).

Módulos previstos: `identity`, `university`, `learning`, `assessment`, `documents`, `analytics`.
Implementado: `health` y `core` (F0); `identity` (registro, login JWT, `/me`, control de rol) y `university` (organigrama, cargos, sistemas, dueños de datos) con su seed (F1).
