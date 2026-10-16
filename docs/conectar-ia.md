# Conectar sua IA ao Specboard

O Specboard não tem IA dentro. Quem mantém o board é a IA que você já usa. Ela só precisa de duas coisas:
saber que o board existe (o prompt) e conseguir fazer requisições HTTP para `http://localhost:8787`.

## Um prompt para qualquer IA

1. Abra http://localhost:8787. A página inicial tem o prompt com o botão **Copiar prompt**.
2. Copie (pelo botão ou selecionando o texto) e cole na sua IA: Claude Code, Cursor, Codex, Gemini CLI,
   Windsurf, Copilot, Aider, ChatGPT… É o mesmo texto para todas.
3. A IA lê o manual em `/llms.txt`, roda o briefing, salva as regras na memória ou no arquivo de instruções
   dela e passa a manter o board.
4. Acompanhe em http://localhost:8787/projetos.

O mesmo texto está em [PROMPT.md](../PROMPT.md) e em `http://localhost:8787/api/agent/prompt` (este já com a
URL e o aviso de token da sua instância).

Se a sua IA não tem memória entre conversas, cole o prompt no começo de cada conversa.

## Testando a conexão

Peça à IA: *"Crie um projeto no Specboard pro que estou fazendo, escreva uma spec curta e registre três
próximos passos."* Ela deve responder com o link do board, e os cards aparecem na interface em até 5 s.

## Dúvidas

**A IA pede confirmação a cada `curl`.** Libere comandos `curl` para `localhost:8787` nas permissões da sua
ferramenta, ou aprove na primeira vez com "não perguntar de novo".

**ChatGPT, Gemini e Claude no navegador.** Eles rodam na nuvem e não alcançam o `localhost` da sua máquina.
Duas saídas:

1. **Sem configurar nada:** cole o prompt. A IA vai te passar os comandos `curl` prontos e você roda no terminal
   (o prompt já pede isso). Funciona, mas dá mais trabalho.
2. **Expor com túnel:** suba um túnel HTTPS (ex.: `cloudflared tunnel --url http://localhost:8787`), defina
   `SPECBOARD_TOKEN` e `SPECBOARD_PUBLIC_URL` com a URL do túnel no `.env`, rode `docker compose up -d` de novo e
   use uma IA que consiga chamar URLs externas. **Nunca exponha sem token.**

Um servidor MCP para essas IAs está no roadmap ([spec.md](../spec.md), seção 7).

**A API não responde.** Rode `docker compose up -d` na pasta do Specboard e confira
http://localhost:8787/api/health.

## Para quem mexe no Specboard

O manual (`/llms.txt`) e o prompt saem de `backend/app/services/agent_docs.py`. Se mudar a API ou o texto,
mude lá e regenere o `PROMPT.md` (o teste `test_prompt_md_matches_default_prompt` acusa a diferença).
