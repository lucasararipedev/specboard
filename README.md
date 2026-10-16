# Specboard

**Kanban spec-first que a sua IA mantém por você.** Sobe com um `docker compose up`, você cola um prompt no
Claude (ou ChatGPT, Gemini, Cursor…) e a partir daí ela registra tarefas, move status, guarda decisões na spec
e te lembra das prioridades no começo de cada sessão, sempre com o link do card.

Feito para devs que querem ser mais organizados e não depender de PO desorganizado para saber o que fazer.

```
você: "amanhã preciso integrar o Stripe, e lembra que o login com Google tá quebrado"
IA:   cria 2 cards (P1 bug no todo, integração no backlog), te manda os links
...
próxima sessão
IA:   "Você tem o bug do login em andamento há 3 dias e o Stripe é o próximo. Seguimos no login?"
```

## Como funciona

- **Um kanban por projeto**: `backlog → todo → doing → blocked → done`, com prioridade, prazo e etiquetas.
- **Spec first**: cada projeto tem uma spec em Markdown que é a fonte da verdade. Decisões entram nela antes
  de virar card, e cada card aponta a seção que implementa.
- **Atividade**: tudo que muda fica registrado, com quem mudou (você ou a IA).
- **Briefing**: um resumo por projeto com lembretes prontos para a IA puxar com você (card parado há dias, P0
  esquecido no backlog, prazo vencido, nada em andamento…).
- **Feito para IA**: manual em `/llms.txt`, prompt padrão, respostas com link, OpenAPI em `/docs`.
- **Sem IA dentro, sem conta, sem chave**: a IA é a que você já usa. Os dados ficam num SQLite na sua máquina.

## Começando

Precisa só de Docker.

```bash
git clone <url-deste-repo> specboard && cd specboard
docker compose up -d          # ou: make up
```

1. Abra http://localhost:8787
2. Vá em **Conectar IA**, copie o prompt e cole na sua IA (o mesmo texto está em [PROMPT.md](PROMPT.md)).
3. Peça: *"crie um projeto no Specboard pro que estou fazendo e registre os próximos passos"*.

Usa Claude Code? Cole também o trecho de memória no seu `~/.claude/CLAUDE.md` e, se quiser, o hook que injeta o
briefing em toda sessão nova. Passo a passo para cada IA em [docs/conectar-ia.md](docs/conectar-ia.md).

## Configuração

Tudo opcional. Para mudar, `cp .env.example .env`, edite e rode `docker compose up -d` de novo.

| Variável | Padrão | Para quê |
|---|---|---|
| `SPECBOARD_PORT` | `8787` | Porta na sua máquina |
| `SPECBOARD_PUBLIC_URL` | `http://localhost:8787` | URL que a IA usa e manda nos links (ajuste junto com a porta) |
| `SPECBOARD_BIND` | `127.0.0.1` | Interface de rede; `0.0.0.0` abre na rede local |
| `SPECBOARD_TOKEN` | vazio | Se definido, a API exige `Authorization: Bearer <token>` |
| `SPECBOARD_STALE_DAYS` | `3` | Dias sem atualização para um card em andamento virar lembrete |

Por padrão só a sua máquina acessa. Se abrir na rede ou num túnel, **defina um token** (`openssl rand -hex 24`).

## Dados e backup

Os dados ficam no volume Docker `specboard-data` (arquivo SQLite). Para backup:

```bash
make backup                                   # ou:
curl -s http://localhost:8787/api/export -o backup.json
```

`docker compose down` mantém os dados; `docker compose down -v` apaga.

## API

A referência para IAs é o [`/llms.txt`](http://localhost:8787/llms.txt): regras, conceitos, endpoints e exemplos
em `curl`. A referência completa (OpenAPI) está em http://localhost:8787/docs. Resumo:

| Rota | Para quê |
|---|---|
| `GET /api/briefing` | Resumo de todos os projetos com lembretes (`?format=json`) |
| `GET/POST /api/projects`, `GET/PATCH/DELETE /api/projects/<slug>` | Projetos e spec |
| `GET/POST /api/projects/<slug>/cards`, `GET/PATCH/DELETE /api/cards/<id>` | Cards |
| `GET/POST /api/projects/<slug>/activity` | Histórico, notas e decisões |
| `GET /api/search?q=` | Busca de cards (para não duplicar) |
| `GET /api/export` | Backup em JSON |

A IA se identifica com o header `X-Actor` (ex.: `claude`), e o histórico mostra quem fez o quê.

## Desenvolvimento

```bash
make dev     # front com hot reload em http://localhost:5173, API em http://localhost:8787
make test    # pytest da API + typecheck e build do front, em containers
```

Sem `make`, os comandos estão no [Makefile](Makefile). Para rodar fora do Docker: `pip install -r
backend/requirements-dev.txt` e `uvicorn app.main:create_app --factory --port 8787 --reload` dentro de
`backend/`; `npm install && npm run dev` dentro de `frontend/`.

```
backend/          FastAPI + SQLAlchemy + SQLite (Python 3.12)
  app/
    main.py         cria a app, registra rotas, serve o front buildado
    config.py       variáveis SPECBOARD_*
    models.py       Project, Card, Activity
    schemas.py      contratos da API (Pydantic)
    api/            rotas: projects, cards, activity, agent (briefing, busca, export, llms.txt, prompt)
    services/       briefing (lembretes), agent_docs (prompt e manual da IA), serialize (respostas com url)
  tests/          pytest
frontend/         Vue 3 + Vite + TypeScript + Vue Router
  src/views/        Projetos, Board (kanban, spec, atividade), Conectar IA
  src/components/   CardModal, MarkdownView
docs/             conectar-ia.md (Claude Code, Cursor, ChatGPT…)
spec.md           a spec deste projeto: problema, escopo da v1, roadmap, decisões
PROMPT.md         o prompt padrão (um teste garante que bate com o servido pela API)
Dockerfile        imagem única: build do front + API
```

Contribuindo com ajuda de IA? O [AGENTS.md](AGENTS.md) tem as convenções do repo.

## Roadmap

O próximo passo grande é a **IA opcional dentro do sistema**: você cadastra uma chave (Claude, ChatGPT, Gemini,
OpenRouter, modelo local) e ganha extração de cards a partir de texto solto, priorização sugerida e resumo
semanal. Também no radar: servidor MCP, integração com GitHub e lembretes por e-mail/Telegram. Detalhes em
[spec.md](spec.md), seção 7.

## Licença

[MIT](LICENSE)
