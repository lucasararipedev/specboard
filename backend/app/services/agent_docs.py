"""Textos para IAs: o prompt que o usuário cola na IA dele e o manual da API (servido em /llms.txt).

O PROMPT.md na raiz do repo é este mesmo prompt com a URL padrão; um teste garante que não divergem.
"""

from ..config import Settings


def agent_prompt(settings: Settings) -> str:
    url = settings.public_url
    auth = (
        "\nA API exige token: mande `Authorization: Bearer <token>` em toda requisição. "
        "O token está no `.env` do Specboard (SPECBOARD_TOKEN); peça para mim se você não tiver.\n"
        if settings.api_token
        else ""
    )
    return f"""Quero que você mantenha meus projetos organizados usando o Specboard, um kanban spec-first que roda na minha máquina.

Endereço: {url}
{auth}
1. Leia agora o manual da API em {url}/llms.txt (com curl ou sua ferramenta de requisição HTTP). Ele tem as regras e os endpoints.
2. Depois rode GET {url}/api/briefing e me diga em poucas linhas o que está em andamento, o que travou e qual deve ser minha próxima prioridade.
3. Daqui pra frente, sem eu precisar pedir:
   - no começo de cada sessão de trabalho, consulte o briefing e me lembre das prioridades e dos lembretes que ele trouxer;
   - tudo que eu mencionar como tarefa, ideia, bug ou plano vira card no projeto certo (procure duplicata antes);
   - mova os cards conforme o trabalho anda (doing ao começar, done ao terminar, blocked se travar) e registre atividades curtas do que foi feito;
   - decisões e mudanças de escopo vão primeiro para a spec do projeto, depois viram cards;
   - quando faltar contexto para planejar ou decidir, registre perguntas para eu responder no board (com opções, se der) em vez de supor, e use minhas respostas assim que eu responder;
   - sempre me mande o link do board ou do card que você criou ou mudou;
   - identifique-se com o header X-Actor (ex.: claude, chatgpt, gemini).
4. Se você tem memória persistente, salve estas regras e o endereço lá para seguir nas próximas conversas (Claude Code: ~/.claude/CLAUDE.md; Cursor: Rules; ChatGPT: Memória ou Instruções personalizadas; Gemini: Gem ou instruções salvas).
5. Se você não consegue fazer requisições HTTP, me avise e me passe os comandos curl prontos para eu rodar. Se a API não responder, peça para eu rodar `docker compose up -d` na pasta do Specboard.
"""


def agent_guide(settings: Settings) -> str:
    url = settings.public_url
    auth_header = ' -H "Authorization: Bearer $SPECBOARD_TOKEN"' if settings.api_token else ""
    auth_note = (
        "Autenticação: toda rota em /api exige `Authorization: Bearer <token>` (SPECBOARD_TOKEN no .env do Specboard)."
        if settings.api_token
        else "Autenticação: desligada (instância local). Se receber 401, peça o token ao usuário."
    )
    h = f'-H "X-Actor: claude"{auth_header}'
    hj = f'{h} -H "Content-Type: application/json"'
    return f"""# Specboard — manual para agentes de IA

O Specboard é um kanban spec-first que roda na máquina do usuário. Você, a IA, mantém o board em dia:
registra tarefas, move status, anota o que foi feito e lembra o usuário das prioridades. O usuário
acompanha pelo navegador e também pode mexer lá.

- API: {url}/api
- Interface: {url} (board de cada projeto em {url}/p/<slug>)
- Docs interativas (OpenAPI): {url}/docs
- {auth_note}

## Regras

1. Comece toda sessão de trabalho com `GET /api/briefing` e resuma para o usuário em poucas linhas:
   o que está em andamento, o que travou e qual a próxima prioridade. Traga os "Lembretes" do briefing.
2. Spec first: a spec do projeto (`GET /api/projects/<slug>/spec`) é a fonte da verdade. Leia antes de
   planejar. Decisões, mudanças de escopo e planos novos entram na spec (`PATCH` com o texto inteiro)
   antes de virar card, e o card aponta a seção em `spec_ref`.
3. Toda tarefa, ideia, bug ou plano que o usuário mencionar vira card. Antes de criar, procure
   duplicata com `GET /api/search?q=...`. Ideia solta vai pro `backlog`; o que é pra já vai pro `todo`.
4. Ao começar algo, mova para `doing`; ao terminar, `done`. Se travar, `blocked` e diga o motivo numa atividade.
5. Registre atividades curtas: o que foi feito (`kind: note`) e o que foi decidido (`kind: decision`).
6. Não suponha o que só o usuário sabe. Quando faltar informação para planejar ou decidir bem, crie uma
   pergunta (`POST /api/projects/<slug>/questions`), objetiva e com 2 a 4 opções quando der. O usuário
   responde na aba Perguntas do board. Se ele responder na conversa, registre você mesmo (`PATCH` com `answer`).
7. "Respostas novas" no briefing são respostas que você ainda não usou: incorpore na spec ou nos cards e
   marque a pergunta com `status: "applied"`. Todo projeto novo já nasce com perguntas iniciais (problema,
   v1, prazo, fora de escopo, tempo disponível); as respostas delas são a base da primeira spec.
8. Mande sempre o header `X-Actor: <seu nome>` (claude, chatgpt, gemini...) para o usuário saber quem mexeu.
9. Depois de criar ou mudar algo, passe ao usuário o link (campo `url` da resposta).
10. Não apague cards nem projetos sem o usuário pedir. Prefira `done` ou arquivar (`archived: true`).
11. Qual projeto usar: compare a pasta ou o repositório atual com os campos `repo` e `slug` de
    `GET /api/projects`. Se nenhum bater, pergunte ao usuário antes de criar um projeto.
12. Seja breve com o usuário. O board guarda os detalhes; a conversa só precisa do essencial e do link.

## Conceitos

- **status**: `backlog` (ideias, sem prioridade) → `todo` (próximos, priorizados) → `doing` → `blocked` → `done`
- **priority**: `0` urgente, `1` alta, `2` normal (padrão), `3` algum dia
- **spec_ref**: seção da spec que o card implementa, ex.: `"3.2 Login"`
- **position**: ordem dentro da coluna (menor fica em cima); ao mudar de status sem informar, o card vai pro fim
- **labels**: lista livre de etiquetas, ex.: `["bug", "front"]`
- **due_date**: prazo opcional `AAAA-MM-DD`; vencidos aparecem no briefing
- **pergunta**: `open` (esperando o usuário) → `answered` (respondida, você ainda não usou) → `applied`
  (você já incorporou); `dismissed` se o usuário dispensar. `options` são respostas sugeridas.

## Endpoints

| Método | Rota | Para quê |
|---|---|---|
| GET | `/api/briefing` | Resumo de todos os projetos com lembretes (Markdown; `?format=json` para JSON) |
| GET | `/api/projects/<slug>/briefing` | Resumo de um projeto |
| GET | `/api/projects` | Lista projetos (`?include_archived=true` para incluir arquivados) |
| POST | `/api/projects` | Cria projeto (já com perguntas iniciais): `{{"name", "slug"?, "summary"?, "spec"?, "repo"?}}` |
| GET | `/api/projects/<slug>` | Projeto com a spec |
| GET | `/api/projects/<slug>/spec` | Só a spec, em Markdown |
| PATCH | `/api/projects/<slug>` | Edita `name`, `summary`, `spec`, `repo`, `archived` |
| GET | `/api/projects/<slug>/cards` | Cards do projeto (`?status=todo` para filtrar) |
| POST | `/api/projects/<slug>/cards` | Cria card: `{{"title", "description"?, "status"?, "priority"?, "labels"?, "spec_ref"?, "due_date"?}}` |
| GET | `/api/cards/<id>` | Um card |
| PATCH | `/api/cards/<id>` | Edita qualquer campo do card (inclui `status` e `position`) |
| DELETE | `/api/cards/<id>` | Apaga (só se o usuário pedir) |
| GET | `/api/projects/<slug>/questions` | Perguntas (`?status=open`, `answered`...) |
| POST | `/api/projects/<slug>/questions` | Pergunta: `{{"question", "context"?, "options"?, "card_id"?}}` |
| PATCH | `/api/questions/<id>` | Responder (`answer`) ou marcar `status: "applied"` |
| GET | `/api/projects/<slug>/activity` | Histórico (`?limit=50&card_id=`) |
| POST | `/api/projects/<slug>/activity` | Registra: `{{"message", "kind": "note"|"decision", "card_id"?}}` |
| GET | `/api/search?q=texto` | Busca cards por título, descrição e spec_ref (`&project=<slug>`) |
| GET | `/api/export` | Backup de tudo em JSON |

Respostas de projeto e card trazem `url`, o link pronto para mandar ao usuário.

## Exemplos

```bash
# Começo de sessão
curl -s {url}/api/briefing{auth_header}

# Criar projeto
curl -s -X POST {url}/api/projects {hj} \\
  -d '{{"name": "Meu SaaS", "summary": "Agenda para barbearias", "repo": "~/code/meu-saas"}}'

# Criar card
curl -s -X POST {url}/api/projects/meu-saas/cards {hj} \\
  -d '{{"title": "Login com Google", "status": "todo", "priority": 1, "spec_ref": "2.1 Autenticação"}}'

# Começar e terminar
curl -s -X PATCH {url}/api/cards/12 {hj} -d '{{"status": "doing"}}'
curl -s -X PATCH {url}/api/cards/12 {hj} -d '{{"status": "done"}}'

# Anotar o que foi feito ou decidido
curl -s -X POST {url}/api/projects/meu-saas/activity {hj} \\
  -d '{{"message": "Escolhemos Stripe em vez de Pagar.me pela API de assinaturas", "kind": "decision"}}'

# Perguntar em vez de supor
curl -s -X POST {url}/api/projects/meu-saas/questions {hj} \
  -d '{{"question": "Cobrança mensal ou anual no lançamento?", "context": "Muda o card de integração com o Stripe", "options": ["Só mensal", "Mensal e anual"]}}'

# Depois de usar a resposta
curl -s -X PATCH {url}/api/questions/7 {hj} -d '{{"status": "applied"}}'

# Atualizar a spec (mande o texto inteiro)
curl -s -X PATCH {url}/api/projects/meu-saas {hj} -d @- <<'EOF'
{{"spec": "# Meu SaaS\\n\\n## 1. Objetivo\\n..."}}
EOF
```

## Modelo de spec (para projeto novo)

```markdown
# <Nome>

## 1. Problema e público
## 2. Escopo da v1
## 3. Fora de escopo
## 4. Decisões
## 5. Perguntas em aberto
```
"""
