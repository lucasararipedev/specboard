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

Endereço: {url} (meus projetos ficam em {url}/projetos)
{auth}
1. Leia agora o manual da API em {url}/llms.txt (com curl ou sua ferramenta de requisição HTTP). Ele tem as regras e os endpoints. Se você suporta MCP, pode usar também o servidor em {url}/mcp: as mesmas regras, como tools.
2. Depois rode GET {url}/api/briefing e me diga em poucas linhas o que está em andamento, o que travou e qual deve ser minha próxima prioridade.
3. Daqui pra frente, sem eu precisar pedir:
   - no começo de cada sessão de trabalho, consulte o briefing e me lembre das prioridades e dos lembretes que ele trouxer;
   - tudo que eu mencionar como tarefa, ideia, bug ou plano vira card no projeto certo (procure duplicata antes);
   - mova os cards conforme o trabalho anda (doing ao começar, done ao terminar, blocked se travar) e registre atividades curtas do que foi feito;
   - decisões e mudanças de escopo vão primeiro para a spec do projeto no Specboard, depois viram cards; na spec, deixe claro o que já existe e o que ainda é plano;
   - o Specboard é meu espaço de planejamento e é privado: ideias, planos e decisões ficam lá. Não copie isso para arquivos do repositório (README, docs, spec.md…) nem faça commit disso sem eu pedir, porque o repositório pode ser público;
   - registre só o que eu disse ou o que você verificou; não invente detalhes, prazos nem decisões, e não descreva como pronto o que ainda é card;
   - quando faltar contexto para planejar ou decidir, registre perguntas para eu responder no board (com opções, se der) em vez de supor, e use minhas respostas assim que eu responder;
   - sempre me mande o link do board ou do card que você criou ou mudou;
   - identifique-se com o header X-Actor (ex.: claude, chatgpt, gemini).
4. Se você tem memória persistente ou um arquivo de instruções, salve um resumo destas regras e o endereço lá para seguir nas próximas conversas sem eu precisar colar este texto de novo.
5. Se você não consegue fazer requisições HTTP, me avise e me passe os comandos curl prontos para eu rodar. Se a API não responder, peça para eu rodar `docker compose up -d` na pasta do Specboard.
"""


def agent_rules() -> str:
    """As regras para a IA: entram no manual (/llms.txt) e nas instruções do MCP."""
    return """1. Comece toda sessão de trabalho com `GET /api/briefing` e resuma para o usuário em poucas linhas:
   o que está em andamento, o que travou e qual a próxima prioridade. Traga os "Lembretes" do briefing.
2. Spec first: a spec do projeto no Specboard (`GET /api/projects/<slug>/spec`) é a fonte da verdade do
   planejamento. Leia antes de planejar. Decisões, mudanças de escopo e planos novos entram nela (`PATCH`
   com o texto inteiro) antes de virar card, e o card aponta a seção em `spec_ref`. É a spec do Specboard,
   não um arquivo do repositório: mesmo que o repo tenha `spec.md` ou docs, não escreva planos lá.
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
    `GET /api/projects`. Se nenhum bater e o usuário disse que está trabalhando nesta pasta, crie o projeto
    com `repo` apontando para ela; se não estiver claro qual é o projeto, pergunte antes de criar.
12. Seja breve com o usuário. O board guarda os detalhes; a conversa só precisa do essencial e do link.
13. O board é privado. Ideias, planos, decisões de negócio e perguntas ficam no Specboard. Não copie para
    arquivos do repositório (README, docs, spec.md, CHANGELOG) nem faça commit disso sem o usuário pedir:
    o repositório pode ser público. Arquivos do repo mudam só quando a tarefa pede e descrevem o que existe.
14. Plano não é fato. Na spec, separe o que já existe do que é planejado; o que não está feito é card,
    não funcionalidade. Registre só o que o usuário disse ou o que você verificou; não invente detalhes,
    prazos nem decisões. Na dúvida, pergunte (regra 6).
15. Etiquetas organizam o board: tipo (`bug`), área (`front`) e versão (`v0.2`) são todas etiquetas. Antes de
    criar uma, veja as que o projeto já usa (`GET /api/projects/<slug>/labels`) e reaproveite a grafia. Para ver
    ou planejar o que entra numa versão, filtre os cards com `?label=v0.2` em vez de ler o board inteiro.
16. Sessão: se o usuário pedir para ligar este chat ao board (`/board`), ligue com `POST /api/sessions` e guarde
    a `key` (no Claude Code o hook já informa a chave no começo do chat). Ao começar cada tarefa, atualize o
    "fazendo agora" com `PATCH /api/sessions/<key>` (`doing`, `card_id`): é o que aparece no painel Agora."""


def board_prompt(argument: str) -> str:
    """O /board: liga o chat, sincroniza a conversa com o board e responde em 3 linhas.

    É o prompt `board` do MCP e o comando do plugin do Claude Code (um teste garante que batem)."""
    return f"""Specboard: sincronize esta conversa com o board e me dê um status curto.

Argumento: {argument}

Se o argumento for "off": desligue este chat do board (tool `session` com action "off", ou
DELETE /api/sessions/<key>), responda só "Specboard desligado neste chat." e pare.

Senão:
1. Ligue este chat ao board (tool `session` com action "on", ou POST /api/sessions). Use a chave de sessão
   que você já tem (no Claude Code o hook informa no começo do chat); se não tiver, guarde a que voltar.
   Projeto: o desta pasta ou o que estamos discutindo; se não estiver claro, pergunte.
2. Leia o briefing do projeto e compare com esta conversa: tarefas, ideias, bugs, decisões, trabalho feito,
   travas e dúvidas.
3. Aplique o que falta, sem pedir licença: cards novos (procure duplicata antes), status (feito, em
   andamento, travado), notas e decisões, a spec, perguntas para o que só eu sei e as etiquetas de cada card
   (inclusive a de versão, como v0.2).
   Registre só o que foi dito ou verificado. Atualize o "fazendo agora" da sessão.
4. Responda em no máximo 3 linhas, sem mais nada:
   Registrei: o que mudou no board (ou "nada novo")
   Esquecendo: o que está parado, vencido ou esperando resposta
   Agora: a próxima ação, com o link do card
"""


def mcp_instructions(settings: Settings) -> str:
    """Instruções que o servidor MCP manda para a IA ao conectar."""
    return f"""Specboard: kanban spec-first que roda na máquina do usuário ({settings.public_url}/projetos). Você mantém
o board em dia pelas tools deste servidor, sem o usuário precisar pedir.

As regras abaixo são as do manual ({settings.public_url}/llms.txt). Onde elas citam uma rota da API, use a
tool equivalente: briefing, list_projects, get_project (traz as etiquetas em uso), save_project, search_cards,
list_cards, save_card, log_activity, save_question e session. O header X-Actor é a configuração do
cliente; o link de cada item vem no campo `url`. Para sincronizar a conversa, use o prompt `board`.

{agent_rules()}
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
- Interface: {url}/projetos (board de cada projeto em {url}/p/<slug>)
- Docs interativas (OpenAPI): {url}/docs
- MCP (Streamable HTTP), para quem prefere tools a curl: {url}/mcp
- {auth_note}

## Regras

{agent_rules()}

## Conceitos

- **status**: `backlog` (ideias, sem prioridade) → `todo` (próximos, priorizados) → `doing` → `blocked` → `done`
- **priority**: `0` urgente, `1` alta, `2` normal (padrão), `3` algum dia
- **spec_ref**: seção da spec que o card implementa, ex.: `"3.2 Login"`
- **position**: ordem dentro da coluna (menor fica em cima); ao mudar de status sem informar, o card vai pro fim
- **labels**: lista livre de etiquetas, ex.: `["bug", "front", "v0.2"]`. Versão é uma etiqueta como outra
  qualquer; o board filtra por uma ou várias (o card precisa ter todas)
- **due_date**: prazo opcional `AAAA-MM-DD`; vencidos aparecem no briefing
- **sessão**: este chat ligado ao board. Tem `key`, projeto e o "fazendo agora" (`doing`, `card_id`), que
  aparecem no painel Agora; sem sinal há 15 min, fica parada.
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
| GET | `/api/projects/<slug>/cards` | Cards do projeto (`?status=todo`; `?label=v0.2&label=front` = com todas as etiquetas) |
| POST | `/api/projects/<slug>/cards` | Cria card: `{{"title", "description"?, "status"?, "priority"?, "labels"?, "spec_ref"?, "due_date"?}}` |
| GET | `/api/projects/<slug>/labels` | Etiquetas em uso, com quantos cards têm cada uma |
| GET | `/api/cards/<id>` | Um card |
| PATCH | `/api/cards/<id>` | Edita qualquer campo do card (inclui `status`, `position` e `labels`, sempre a lista inteira) |
| DELETE | `/api/cards/<id>` | Apaga (só se o usuário pedir) |
| GET | `/api/projects/<slug>/questions` | Perguntas (`?status=open`, `answered`...) |
| POST | `/api/projects/<slug>/questions` | Pergunta: `{{"question", "context"?, "options"?, "card_id"?}}` |
| PATCH | `/api/questions/<id>` | Responder (`answer`) ou marcar `status: "applied"` |
| GET | `/api/projects/<slug>/activity` | Histórico (`?limit=50&card_id=`) |
| POST | `/api/projects/<slug>/activity` | Registra: `{{"message", "kind": "note"|"decision", "card_id"?}}` |
| GET | `/api/search?q=texto` | Busca cards por título, descrição e spec_ref (`&project=<slug>`, `&label=`) |
| GET | `/api/sessions` | Painel Agora: sessões ligadas (`?project=<slug>`) |
| POST | `/api/sessions` | Liga este chat: `{{"key"?, "project"?, "cwd"?, "doing"?, "card_id"?}}` (devolve a `key`) |
| PATCH | `/api/sessions/<key>` | Atualiza o "fazendo agora": `{{"doing", "card_id"?}}` |
| DELETE | `/api/sessions/<key>` | Desliga este chat |
| GET | `/api/profile` | Nome do usuário (para chamar pelo nome) |
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

# Versão é etiqueta: ver as que existem, pôr um card na v0.2 e ver só as entregas dela
curl -s {url}/api/projects/meu-saas/labels{auth_header}
curl -s -X PATCH {url}/api/cards/12 {hj} -d '{{"labels": ["pagamentos", "v0.2"]}}'
curl -s "{url}/api/projects/meu-saas/cards?label=v0.2"{auth_header}

# Ligar este chat ao board e dizer o que está fazendo
curl -s -X POST {url}/api/sessions {hj} -d '{{"project": "meu-saas", "doing": "Integrando o Stripe", "card_id": 12}}'

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

## Sincronizar a conversa (/board)

Quando o usuário pedir `/board` (ou "atualiza o board"), siga isto:

{board_prompt("o que o usuário passou depois de /board (ex.: off), ou nada")}
## Modelo de spec (para projeto novo)

Marque o que já está pronto (ex.: "(feito)") e deixe planos no roadmap ou nos cards.

```markdown
# <Nome>

## 1. Problema e público
## 2. Escopo da v1
## 3. Fora de escopo
## 4. Decisões
## 5. Perguntas em aberto
```
"""
