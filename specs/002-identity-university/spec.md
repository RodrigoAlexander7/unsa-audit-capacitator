# Spec 002 — Identity + University

**Estado:** aprobada (plan v2, Fase 1)

## Objetivo
Que las personas puedan registrarse e iniciar sesión, que exista un superadmin definido por `.env`, y que la aplicación disponga de la **BD ficticia de la UNSA** (organigrama, cargos, personas, sistemas, dueños de datos y actividades de tratamiento) consultable por API y visible en una página de la UI.

## Historias
- **H1.** Como participante quiero registrarme e iniciar sesión para acceder a la plataforma.
- **H2.** Como superadmin quiero que mi cuenta exista desde el seed con el email del `.env`, sin que nadie más pueda reclamarlo.
- **H3.** Como participante autenticado quiero explorar el organigrama de la UNSA, sus cargos y titulares.
- **H4.** Como participante quiero ver los sistemas de la universidad y quién es dueño/responsable de sus datos.
- **H5.** Como equipo quiero un seed reproducible con datos ficticios para el resto de las fases.

## Decisión de seguridad (superadmin)
El rol `superadmin` pertenece a la cuenta cuyo email es `SUPERADMIN_EMAIL`. Para evitar que un tercero reclame ese email registrándose, **el registro público rechaza ese email**; la cuenta se crea solo desde el seed/comando `EnsureSuperadmin` usando `SUPERADMIN_PASSWORD` del `.env`.

## Criterios de aceptación
### Identity
- **AC-002-1** *Given* un email no registrado y password de ≥ 8 caracteres, *When* `POST /auth/register`, *Then* 201 con el usuario (rol `learner`) y sin ningún campo de password/hash.
- **AC-002-2** *Given* un email ya registrado (sin distinguir mayúsculas), *When* se registra de nuevo, *Then* 409.
- **AC-002-3** *Given* `SUPERADMIN_EMAIL`, *When* alguien intenta registrarlo por API, *Then* 409 con el mismo mensaje que un email duplicado.
- **AC-002-4** *Given* password < 8 caracteres o email mal formado, *When* se registra, *Then* 422.
- **AC-002-5** *Given* credenciales válidas, *When* `POST /auth/login`, *Then* 200 con `access_token` (Bearer) y rol; *Given* password errónea o email inexistente, *Then* 401 con el mismo mensaje genérico.
- **AC-002-6** *Given* un token válido, *When* `GET /me`, *Then* 200 con el perfil; sin token, token inválido o expirado → 401.
- **AC-002-7** *Given* `SUPERADMIN_EMAIL` y `SUPERADMIN_PASSWORD`, *When* corre el seed, *Then* existe un usuario `superadmin` con ese email; ejecutarlo dos veces no duplica y puede iniciar sesión.
- **AC-002-8** *Given* un endpoint solo-superadmin (`GET /admin/ping`), *When* lo llama un `learner`, *Then* 403; un `superadmin` → 200; sin token → 401.
- **AC-002-9** *Given* la BD, *When* inspecciono `users`, *Then* el password está almacenado como hash Argon2, nunca en texto plano.

### University
- **AC-002-10** *Given* el seed ejecutado, *Then* existen: 1 rectorado, 2 vicerrectorados, 4 facultades, 12 escuelas (≥ 25 unidades en total incluyendo oficinas), ≥ 60 personas, 8 sistemas y 10 actividades de tratamiento; ejecutarlo dos veces no duplica y todas las referencias son consistentes.
- **AC-002-11** *Given* un usuario autenticado, *When* `GET /org-units`, *Then* 200 con el árbol anidado cuya raíz es el rectorado; sin token → 401.
- **AC-002-12** *Given* una unidad existente, *When* `GET /org-units/{id}`, *Then* 200 con la unidad, su unidad padre, hijas, y cargos con su titular; id inexistente → 404.
- **AC-002-13** *Given* un usuario autenticado, *When* `GET /systems`, *Then* 200 con cada sistema, su unidad dueña, categorías de datos y responsables con rol (`controller`/`processor`/`steward`).

### Transversales
- **AC-002-14** *Given* `contracts/openapi.yaml`, *Then* la API expone todos sus paths y métodos.
- **AC-002-15** Los módulos nuevos cumplen AC-001-5 (sin frameworks en `domain`/`application`).
- **AC-002-16** *Given* la UI, *When* me registro, inicio sesión, abro `/university` y cierro sesión, *Then* el flujo funciona; `/university` sin sesión redirige a `/login`; el token no es accesible desde JS (cookie `httpOnly`).

## Fuera de alcance
Vincular `users` con `people`, recuperación de contraseña, refresh tokens, edición del organigrama, endpoint de actividades de tratamiento (se consume en fases posteriores; solo tabla + seed).

## Datos del seed (ficticios)
Universidad Nacional de San Agustín (ficticia): Rectorado; Vicerrectorados Académico y de Investigación; 4 facultades × 3 escuelas; oficinas: Registros Académicos, Tecnologías de la Información, Recursos Humanos, Secretaría General, Biblioteca Central, Bienestar Universitario, Control Institucional. Personas con nombres inventados.
