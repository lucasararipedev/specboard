# Specboard — spec

> Ideia registrada em 2026-10-16. Status: v1 implementada. Nome provisório.

## 1. Problema

Quem toca projeto próprio (side project, SaaS, freela) ou trabalha num time sem um PO organizado perde o fio
com facilidade: ideias espalhadas em notas, prioridades só na cabeça, decisões esquecidas, tarefa começada e
largada. Esse dev já usa IA o dia inteiro, mas a IA esquece tudo entre uma sessão e outra, e ferramentas como
Jira, Linear e Trello dão trabalho manual demais para manter atualizadas sozinho.

## 2. Público

- **Principal:** devs que querem ser mais organizados e não depender de PO desorganizado para saber o que fazer.
- Também: founders técnicos organizando ideias e projetos do zero.
- Perfil: roda Docker, usa Claude Code, Cursor, Codex, ChatGPT ou similar no dia a dia.

## 3. Proposta

Um kanban **spec-first**, open source e self-hosted (um `docker compose up`), feito para **a IA do usuário
operar**. O usuário cola um prompt padrão na IA dele; a partir daí a IA:

- registra tarefas, ideias, bugs e planos como cards;
- move status conforme o trabalho anda e anota o que foi feito;
- guarda decisões e mudanças de escopo na spec do projeto;
- no começo de cada sessão, lê o briefing e lembra o usuário das prioridades;
- sempre passa o link do board ou do card para o usuário ver.

Um kanban por projeto. O humano acompanha e corrige pela interface; a IA faz o trabalho chato de manter tudo
em dia.

## 4. Princípios

1. **Spec first.** Cada projeto tem uma spec em Markdown que é a fonte da verdade. Decisão entra na spec antes
   de virar card, e o card aponta a seção que implementa (`spec_ref`).
2. **A IA opera, o humano revisa.** Interface simples para acompanhar e ajustar, não para preencher formulário.
3. **Agnóstico de IA.** HTTP + JSON + Markdown, com o manual em `/llms.txt`. Qualquer IA que faz requisições
   HTTP usa; a que não faz entrega os comandos `curl` para o usuário rodar.
4. **Zero atrito.** Um container, SQLite, sem conta, sem chave de IA na v1.
5. **Os dados são do usuário.** Ficam na máquina dele, com export em JSON.

## 5. Escopo da v1 (feito)

### 5.1 Projetos
Nome, slug (gerado do nome), resumo, repositório (caminho ou URL, para a IA achar o projeto certo), spec em
Markdown, arquivar.

### 5.2 Kanban
- Status fixos: `backlog` → `todo` → `doing` → `blocked` → `done`. Fixos de propósito: a IA precisa de um
  vocabulário estável.
- Prioridade 0 a 3 (P0 urgente, P3 algum dia), etiquetas, `spec_ref`, prazo, descrição em Markdown.
- Ordem dentro da coluna (`position` float, insere entre dois cards sem renumerar).
- `started_at` e `done_at` mantidos automaticamente pelo status.
- Interface com arrastar e soltar, criação rápida por coluna e card aberto por link (`/p/<slug>?card=<id>`).

### 5.3 Atividade
- Registro automático: projeto e card criados, mudança de status, spec atualizada, card apagado.
- Registro manual: notas (`note`) e decisões (`decision`), ligadas ou não a um card.
- Autor de cada ação pelo header `X-Actor` (`claude`, `chatgpt`...; a interface manda `user`).

### 5.4 Briefing com lembretes
`GET /api/briefing` (Markdown ou JSON) por projeto ativo: em andamento, travado, próximos 5 do todo, contagens,
feitos nos últimos 7 dias, última atividade e **lembretes** para a IA puxar com o usuário:

- projeto sem spec;
- nada em andamento com fila no todo (sugere o próximo);
- todo vazio (ajudar a priorizar o backlog);
- mais de 3 cards em andamento (WIP alto);
- card em `doing`/`blocked` sem atualização há `SPECBOARD_STALE_DAYS` dias;
- prazo vencido;
- P0/P1 esquecido no backlog;
- projeto sem atividade há 7 dias.

### 5.5 Feito para IA
- `/llms.txt`: manual com regras, conceitos, endpoints e exemplos, com a URL da instância.
- `/api/agent/prompt` e `PROMPT.md`: o prompt padrão para colar na IA (um teste garante que os dois batem).
- Busca (`/api/search`) para a IA evitar card duplicado.
- Toda resposta de projeto e card traz `url` pronta para mandar ao usuário.
- OpenAPI em `/docs`.

### 5.6 Interface (Vue 3)
Lista de projetos, board, aba da spec (ver e editar), aba de atividade, modal do card com histórico e a
página "Conectar IA" com o prompt e o trecho para o `CLAUDE.md`. O board consulta a API a cada 5 s para
mostrar o que a IA mudou. Tema claro e escuro.

### 5.7 Segurança
Porta presa em `127.0.0.1` por padrão. `SPECBOARD_TOKEN` opcional exige `Authorization: Bearer` em toda a API
(menos health, manual e prompt, que não têm dados). O prompt nunca inclui o token. Markdown renderizado é
sanitizado (DOMPurify), porque a IA pode trazer conteúdo da web.

### 5.8 Infra
Imagem única (build do Vue + FastAPI servindo front e API na porta 8787), volume para o SQLite,
`docker-compose.dev.yml` com hot reload, testes de API com pytest, `make backup` via export.

## 6. Fora da v1

IA dentro do sistema, login e multiusuário, notificações, integrações (GitHub etc.), servidor MCP, colunas
customizáveis, subtarefas.

## 7. Roadmap

### v2 — IA opcional dentro do sistema
- O usuário cadastra a chave que quiser: Claude (Anthropic), ChatGPT (OpenAI), Gemini, Jev/TypeSafe,
  OpenRouter ou um modelo local (Ollama). Chave criptografada no banco; tudo continua funcionando sem chave.
- Usos:
  - **extração**: colar texto solto (brain dump, notas de reunião, conversa) e virar cards + atualização da spec;
  - priorização sugerida e quebra de card grande em subtarefas;
  - detecção de duplicatas e de cards que contradizem a spec;
  - resumo semanal do que andou e do que travou;
  - chat dentro do board.
- Escolher a IA por tarefa (uma barata para classificar, uma melhor para extrair).

### Outras ideias
- **Hook de início de sessão** pronto para o Claude Code (o briefing entra no contexto sozinho). Já documentado
  em `docs/conectar-ia.md`; avaliar um instalador.
- Servidor MCP, para IAs sem shell (Claude Desktop, claude.ai com conector) usarem sem `curl`.
- Lembretes ativos fora da IA: resumo diário por e-mail, Telegram ou notificação do sistema.
- GitHub: commit/PR com `closes #12` fecha o card; link de PR no card.
- Subtarefas/checklist e dependências entre cards.
- Histórico de versões da spec com diff.
- Import do backup (o export já existe) e de Trello, Linear e GitHub Issues.
- Métricas: lead time, throughput, tempo parado.
- Multiusuário para times pequenos.
- Interface e docs em inglês para alcance open source.
- Migrações com Alembic quando o esquema mudar (hoje é `create_all`).

## 8. Decisões

- **SQLite + `create_all`** na v1: um arquivo, zero serviço extra. Outro banco via `SPECBOARD_DATABASE_URL`.
- **Polling de 5 s** em vez de websocket: simples e suficiente para um usuário.
- **Um container** servindo front e API: uma porta, e o link que a IA manda é o mesmo que o humano abre.
- **Status fixos** em inglês na API (vocabulário estável para qualquer IA), rótulos em português na interface.
- **Sem IA dentro na v1**: a IA de fora já resolve o fluxo principal e evita pedir chave logo de cara.
- Licença MIT.

## 9. Perguntas em aberto

- IAs que só rodam no navegador (ChatGPT, claude.ai) não alcançam `localhost`. Caminho: MCP remoto, túnel
  documentado ou uma versão hospedada?
- Como garantir que a IA atualize o board sem o usuário lembrar? Hoje: prompt + memória da IA + hook de
  sessão no Claude Code. Medir na prática.
- Nome definitivo do projeto.
