# Spec 008 — Pulido, datos demo y cierre

**Estado:** aprobada (plan v2, Fase 7)

## Objetivo
Dejar el sistema **listo para probar**: datos demo realistas (participantes con distintos avances) para que el panel del superadmin y el asesor IA tengan qué analizar, pruebas end-to-end del recorrido principal, verificación de accesibilidad, un comando para levantar todo y una guía de demo reproducible en menos de 10 minutos.

## Historias
- **H1.** Como evaluador quiero abrir el panel del superadmin y ver estadísticas con sentido sin tener que crear datos a mano.
- **H2.** Como evaluador quiero entrar como participante demo en distintos puntos del recorrido (recién matriculado, a mitad, avanzado).
- **H3.** Como equipo quiero un único comando para levantar base de datos, migraciones, seed, API y web.
- **H4.** Como equipo quiero pruebas E2E y de accesibilidad que protejan el recorrido principal.

## Reglas
1. El seed demo es **opcional** (`--demo`), idempotente y solo toca cuentas con email `@demo.unsa.example`. `--reset-demo` las elimina (y las de pruebas E2E `@e2e.unsa.example`) y las recrea.
2. Todos los participantes demo comparten la contraseña documentada `Demo-1234` (dato ficticio, solo POC).
3. El seed demo usa los **casos de uso reales** (matrícula, intentos, evaluaciones) con reloj inyectado y respuestas generadas por un solucionador, de modo que las estadísticas son consistentes con las reglas del sistema.
4. El cohorte demo cubre: ruta completada hasta R3, hasta R2, solo R1, R1 a medias con módulos fallidos (módulos difíciles), participantes **estancados** (sin actividad en más de 7 días), matriculados sin intentos, registrados sin matrícula, y evaluaciones controller/processor aprobadas y no aprobadas.

## Criterios de aceptación
- **AC-008-1** *Given* una BD migrada y con el seed base, *When* `python -m unsa_audit.seed --demo`, *Then* se crean 12 participantes demo con la contraseña documentada y los avances descritos; ejecutarlo de nuevo no duplica nada.
- **AC-008-2** *Given* el seed demo, *When* el superadmin consulta `/admin/stats/routes`, *Then* ve ≥ 10 matriculados en R1, ≥ 3 completados en R1, ≥ 1 completado en R2 y R3, ≥ 2 estancados y ≥ 1 módulo difícil; `/admin/stats/assessments` tiene ambos perfiles con competencias; y el snapshot sigue sin datos personales.
- **AC-008-3** *Given* `--reset-demo`, *Then* se eliminan solo las cuentas `@demo.unsa.example` y `@e2e.unsa.example` (con su progreso) y se recrea el cohorte; las demás cuentas, incluido el superadmin, no cambian.
- **AC-008-4** *Given* el stack levantado, *When* corre la suite E2E (Playwright), *Then* pasan: registro → matrícula → módulo con ejercicio → resultado; login del participante demo y acceso a `/routes`; un participante no accede a `/admin`; login del superadmin → panel con estadísticas; documentos: diff y matriz PIMS; evaluación controller completa hasta ver resultados por competencia.
- **AC-008-5** *Given* las páginas principales (login, rutas, matriz PIMS, panel admin), *Then* axe-core no reporta violaciones de impacto *serious* o *critical*.
- **AC-008-6** *Given* el repo, *Then* `make dev` levanta Postgres, aplica migraciones, carga el seed (con demo) y arranca API y web, y el README y `docs/demo.md` describen cómo probar.
- **AC-008-7** *(manual, `agy` real)* Con los datos demo, la pregunta «¿Cómo están los alumnos de sensibilización?» devuelve un diagnóstico que cita cifras del cohorte demo.

## Fuera de alcance
Despliegue en producción, CI en un servidor, datos demo configurables por el usuario, pruebas de carga.
