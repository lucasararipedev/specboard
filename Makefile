# Atalhos. Sem make, rode os comandos do lado direito direto.
DEV = docker compose -f docker-compose.dev.yml
# Endereço do app: SPECBOARD_PUBLIC_URL do .env, ou o padrão.
URL = $$(grep -s '^SPECBOARD_PUBLIC_URL=' .env | cut -d= -f2- | grep . || echo http://localhost:8787)

.PHONY: up down link logs dev dev-down test build backup

up:            ## sobe o Specboard e mostra o link
	docker compose up -d --build
	@for i in $$(seq 20); do curl -sf --max-time 1 "$(URL)/api/health" >/dev/null && break; sleep 0.5; done
	@$(MAKE) --no-print-directory link

link:          ## mostra o link do Specboard (e avisa se está fora do ar)
	@url=$(URL); if curl -sf --max-time 2 "$$url/api/health" >/dev/null; then echo "$$url"; \
	else echo "$$url (fora do ar: rode make up)"; fi

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
