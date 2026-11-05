# Guía de demo (≈ 10 minutos)

Todos los datos son ficticios. Arranque: `make dev` (Postgres + migraciones + seed con cohorte demo + API + web) y abre <http://localhost:5173>.

## Cuentas

| Rol | Usuario | Contraseña |
|---|---|---|
| Superadmin | `SUPERADMIN_EMAIL` de `.env` (por defecto `superadmin@unsa-poc.example`) | `SUPERADMIN_PASSWORD` de `.env` |
| Participantes demo | `<nombre>@demo.unsa.example` (tabla siguiente) | `Demo-1234` |

## El cohorte demo

| Participante | Situación |
|---|---|
| `ana.quispe` | Completó R1, R2 y R3; matriculada en R4; evaluación controller aprobada |
| `luis.mamani` | Completó R1 y R2; en R3; evaluación controller 67 % (no aprobada) |
| `rosa.condori` | Completó R1; evaluación processor aprobada |
| `silvia.herrera` | Completó R1, matriculada en R2; evaluación processor 33 % |
| `pedro.bellido` | R1 con 6 módulos aprobados; falló la evaluación final |
| `andres.nunez` | R1 con 6 módulos aprobados, sin evaluación final (reciente) |
| `jorge.caceres` | R1 con 5 módulos; falla «Riesgos cotidianos» dos veces (módulo difícil) |
| `lucia.valdivia` | R1 con 3 módulos; falla «Datos y sistemas» dos veces; **estancada** |
| `carmen.delgado` | R1 con 4 módulos hace 12 días; evaluación controller 42 %; **estancada** |
| `miguel.zuniga` | R1 con 2 módulos |
| `elena.medina` | Matriculada en R1 hace 14 días sin ningún intento; **estancada** |
| `raul.fuentes` | Registrado, sin matrícula |

## Recorrido sugerido

1. **Participante (2 min)** — entra como `ana.quispe@demo.unsa.example`. En *Mis rutas* ve 3 rutas aprobadas (52 h acreditadas) y la Ruta 4 (*Auditor interno*, 32 h) disponible con sus 10 módulos activos. Abre *R2 → Contexto y alcance*, *R3 → Plan de tratamiento* o *R4 → Listas de verificación* / *Informe y seguimiento* para ver el panel lado a lado y la corrección determinista.
2. **Ejercicio práctico (2 min)** — como `miguel.zuniga`, abre un módulo de R1 pendiente (p. ej. *Riesgos cotidianos*), responde mal a propósito y lee la retroalimentación; el módulo final queda bloqueado hasta aprobar los demás.
3. **Documentos versionados (2 min)** — *Documentos → ROF → Diferencias* (v1 → v3). *Proponer cambio* y, con el superadmin, aprobarlo o rechazarlo (si la base cambió → conflicto 409).
4. **PIMS (1 min)** — *Documentos → Conjunto documental del PIMS (ISO/IEC 27701)*: 11 requisitos con estados vigente / borrador / vencido / sin responsable / faltante.
5. **Evaluación controller / processor (1 min)** — *Evaluación*: 12 preguntas, resultados por competencia y por requisito del PIMS.
6. **Superadmin y asesor IA (2 min)** — entra como superadmin → *Panel*: estadísticas por ruta, módulos más difíciles, estancados y evaluaciones. En *Asesor IA* pregunta «¿Cómo están los alumnos de sensibilización?»: la respuesta (≈ 10 s, vía `agy`) cita las cifras del cohorte y propone ajustes al plan de enseñanza. El *snapshot* que recibe el asesor es agregado y anónimo (ver `/admin/advisor/snapshot.json`).

## Reiniciar el cohorte

```bash
cd backend && uv run python -m unsa_audit.seed --reset-demo   # elimina @demo y @e2e y recrea el cohorte
```

Las pruebas E2E (`cd frontend && npm run test:e2e`) crean cuentas `@e2e.unsa.example`; `--reset-demo` las limpia.
