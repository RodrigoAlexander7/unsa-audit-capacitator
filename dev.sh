#!/usr/bin/env bash
# Levanta todo el POC para probar: Postgres, migraciones, seed (con cohorte demo), API y web.
#   ./dev.sh              arranca (idempotente)
#   ./dev.sh --reset-demo recrea el cohorte demo y elimina cuentas de pruebas E2E
# Ctrl+C detiene API y web (la base de datos sigue arriba: `docker compose stop db`).
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(pwd)"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "→ Creé .env desde .env.example (valores de desarrollo; cámbialos fuera de un POC)."
fi

SEED_ARGS=(--demo)
[[ "${1:-}" == "--reset-demo" ]] && SEED_ARGS=(--reset-demo)

echo "→ PostgreSQL"
docker compose up -d --wait db

echo "→ Dependencias, migraciones y seed"
(cd backend && uv sync --quiet && uv run alembic upgrade head && uv run python -m unsa_audit.seed "${SEED_ARGS[@]}")
[[ -d frontend/node_modules ]] || (cd frontend && npm install --no-audit --no-fund)

cleanup() {
  echo
  echo "→ Deteniendo API y web"
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "${WEB_PID:-}" ]] && kill "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "→ API en http://localhost:8000 y web en http://localhost:5173"
(cd "$ROOT/backend" && exec uv run uvicorn unsa_audit.main:app --port 8000) &
API_PID=$!
(cd "$ROOT/frontend" && exec npm run dev -- --port 5173 --strictPort) &
WEB_PID=$!

cat <<EOF

  Listo para probar:  http://localhost:5173
  Superadmin:   (SUPERADMIN_EMAIL / SUPERADMIN_PASSWORD de .env)
  Participantes demo: ana.quispe@demo.unsa.example  /  Demo-1234   (guía: docs/demo.md)

EOF
wait
