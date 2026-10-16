# Atalhos. Sem make, rode os comandos do lado direito direto.
DEV = docker compose -f docker-compose.dev.yml

.PHONY: up down logs dev dev-down test build backup

up:            ## sobe o Specboard em http://localhost:8787
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

dev:           ## hot reload: front em :5173, API em :8787
	$(DEV) up

dev-down:
	$(DEV) down

test:          ## testes da API + typecheck/build do front
	$(DEV) run --rm --no-deps api sh -c "pip install -q --root-user-action=ignore -r requirements-dev.txt && pytest -q"
	$(DEV) run --rm --no-deps web sh -c "npm ci --no-audit --no-fund && npm run typecheck && npx vite build --outDir /tmp/dist --emptyOutDir"

backup:        ## exporta tudo para backup-AAAA-MM-DD.json
	curl -sf http://localhost:8787/api/export -o backup-$$(date +%F).json && echo "salvo em backup-$$(date +%F).json"
