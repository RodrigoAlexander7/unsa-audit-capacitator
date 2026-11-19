.DEFAULT_GOAL := help
.PHONY: help dev setup env db install migrate seed demo reset-demo api web stop \
        lint check test test-e2e verify

API_PORT ?= 8000
WEB_PORT ?= 5173

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-12s %s\n", $$1, $$2}'

# --------------------------------------------------------------------- arranque

dev: setup ## Levanta todo para probar (BD + migraciones + seed demo + API + web)
	@echo ""
	@echo "  Web:        http://localhost:$(WEB_PORT)"
	@echo "  API:        http://localhost:$(API_PORT)/docs"
	@echo "  Superadmin: SUPERADMIN_EMAIL / SUPERADMIN_PASSWORD de .env"
	@echo "  Demo:       ana.quispe@demo.unsa.example / Demo-1234   (guía: docs/demo.md)"
	@echo ""
	@$(MAKE) -j2 --no-print-directory api web

setup: env db install migrate demo ## Prepara BD, dependencias, migraciones y datos (sin arrancar servidores)

env:
	@test -f .env || (cp .env.example .env && echo "→ Creé .env desde .env.example (valores de desarrollo)")

db: env ## Levanta PostgreSQL (puerto 5433)
	docker compose up -d --wait db

install: ## Instala dependencias de backend y frontend
	cd backend && uv sync --quiet
	cd frontend && npm install --no-audit --no-fund

migrate: ## Aplica las migraciones de Alembic
	cd backend && uv run alembic upgrade head

seed: ## Seed base: universidad, rutas, documentos y superadmin
	cd backend && uv run python -m unsa_audit.seed

demo: ## Seed base + 12 participantes demo (idempotente)
	cd backend && uv run python -m unsa_audit.seed --demo

reset-demo: ## Elimina cuentas @demo y @e2e y recrea el cohorte demo
	cd backend && uv run python -m unsa_audit.seed --reset-demo

api: ## Arranca solo la API
	cd backend && uv run uvicorn unsa_audit.main:app --port $(API_PORT)

web: ## Arranca solo la web
	cd frontend && npm run dev -- --port $(WEB_PORT) --strictPort

stop: ## Detiene PostgreSQL (los datos se conservan)
	docker compose stop db

# --------------------------------------------------------------- verificación

lint: ## ruff + pyright + prettier
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright
	cd frontend && npx prettier --check src e2e playwright.config.ts vite.config.ts

check: ## svelte-check del frontend
	cd frontend && npm run check

test: ## Tests de backend (requiere BD) y de frontend
	cd backend && uv run pytest -q
	cd frontend && npm test

test-e2e: ## E2E + accesibilidad con Playwright (usa Chrome del sistema)
	cd frontend && npm run test:e2e

verify: lint check test test-e2e ## Todo lo anterior
	cd backend && uv run alembic check
	cd frontend && npm run build
