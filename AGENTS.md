# AGENTS.md — convenções para quem (humano ou IA) mexe neste repositório

Este arquivo é sobre **desenvolver o Specboard**. Para usar o Specboard como kanban, veja `PROMPT.md` e
`/llms.txt`.

## Spec first

`spec.md` é a fonte da verdade do produto. Mudança de comportamento, escopo ou decisão entra na spec no mesmo
commit do código (escopo da v1 na seção 5, roadmap na 7, decisões na 8).

## Estrutura e comandos

- Backend: `backend/` (FastAPI, SQLAlchemy 2, SQLite, Python 3.12). App criada por `app.main:create_app`
  (uvicorn com `--factory`).
- Frontend: `frontend/` (Vue 3, Vite, TypeScript, Vue Router, CSS puro com variáveis; sem framework de UI).
- `make dev` sobe com hot reload; `make test` roda pytest e o build do front (com `vue-tsc`).

## Regras

- **A API é a interface da IA.** Ao criar ou mudar endpoint ou campo, atualize junto:
  `backend/app/services/agent_docs.py` (manual `/llms.txt`), a tabela do `README.md` e os testes.
- **O prompt tem duas cópias.** `PROMPT.md` precisa ser igual a `agent_prompt(Settings())`. Se mudar o texto em
  `agent_docs.py`, regenere o arquivo; o teste `test_prompt_md_matches_default_prompt` acusa a diferença.
- Respostas de projeto e card sempre trazem `url` (montada em `services/serialize.py`).
- Mudança de status, criação e exclusão geram `Activity` automaticamente; o autor vem do header `X-Actor`.
- Datas sempre em UTC com fuso (`UTCDateTime` em `db.py`).
- Status são fixos (`models.STATUSES`) e em inglês na API; rótulos em português só na interface (`types.ts`).
- Markdown vindo da API é renderizado só via `MarkdownView.vue` (sanitizado com DOMPurify).
- Textos de interface e docs em português do Brasil.
- Esquema do banco: `create_all` na v1. Ao mudar uma tabela existente, introduza Alembic em vez de quebrar
  bancos já criados.
