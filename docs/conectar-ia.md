# Conectar sua IA ao Specboard

O Specboard não tem IA dentro. Quem mantém o board é a IA que você já usa. Ela só precisa de duas coisas:
saber que o board existe e conseguir falar com `http://localhost:8787`, por MCP ou por HTTP (`curl`).

## Claude Code: o plugin

O caminho mais curto. Com o Specboard no ar, no terminal:

```bash
curl -fsSL http://localhost:8787/install/claude-code.sh | sh       # Linux, macOS, WSL, Git Bash
irm http://localhost:8787/install/claude-code.ps1 | iex            # Windows (PowerShell)
```

O instalador acha o Claude Code no terminal ou dentro da extensão do VS Code e do Cursor (que não põe o comando
`claude` no terminal) e instala o plugin. Depois, abra um chat novo. Comandos e o que acontece sozinho:
[README, Plugin do Claude Code](../README.md#plugin-do-claude-code).

Mexendo no Specboard e quer testar o plugin da sua cópia local? Na pasta do repositório:
`claude plugin marketplace add ./` e `claude plugin install specboard@specboard`.

O plugin traz:

- **MCP** em `http://localhost:8787/mcp`, com as regras do manual como instruções e as ações como tools;
- **`/board`**: liga o chat ao board, confere a conversa contra o board, registra o que faltou e responde em 3
  linhas (o que registrou, o que você está esquecendo, o que fazer agora). `/board off` desliga;
- **hooks**: ao abrir um chat numa pasta que é o `repo` de um projeto, o chat já começa ligado e recebe o
  briefing; a cada resposta ele dá sinal de vida e, ao fechar, sai do painel **Agora** (em `/projetos`).

Endereço ou token diferentes? Defina `SPECBOARD_URL` e `SPECBOARD_TOKEN` no ambiente antes de abrir o Claude Code.

## Outras ferramentas com MCP

Cursor, VS Code e outras que aceitam MCP por HTTP: cadastre a URL `http://localhost:8787/mcp`. Mande o header
`X-Actor` com o nome da IA (ex.: `cursor`) para o histórico mostrar quem mexeu; sem ele, vale o nome que o
cliente informa. Com `SPECBOARD_TOKEN` definido, mande também `Authorization: Bearer <token>`.

Exemplo para o Cursor (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "specboard": { "url": "http://localhost:8787/mcp", "headers": { "X-Actor": "cursor" } }
  }
}
```

Para ligar um chat ao painel Agora fora do Claude Code, peça "liga este chat ao Specboard" ou use o prompt
`board` do servidor (algumas ferramentas mostram como comando).

## Um prompt para qualquer IA (sem MCP)

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

**Quero sincronizar uma conversa sem MCP.** Peça "atualiza o board": o manual (`/llms.txt`) tem a seção
*Sincronizar a conversa*, o mesmo roteiro do `/board`.

**A IA pede confirmação a cada `curl`.** Libere comandos `curl` para `localhost:8787` nas permissões da sua
ferramenta, ou aprove na primeira vez com "não perguntar de novo".

**ChatGPT, Gemini e Claude no navegador.** Eles rodam na nuvem e não alcançam o `localhost` da sua máquina.
Duas saídas:

1. **Sem configurar nada:** cole o prompt. A IA vai te passar os comandos `curl` prontos e você roda no terminal
   (o prompt já pede isso). Funciona, mas dá mais trabalho.
2. **Expor com túnel:** suba um túnel HTTPS (ex.: `cloudflared tunnel --url http://localhost:8787`), defina
   `SPECBOARD_TOKEN` e `SPECBOARD_PUBLIC_URL` com a URL do túnel no `.env`, rode `docker compose up -d` de novo e
   use uma IA que consiga chamar URLs externas. **Nunca exponha sem token.**

O MCP não resolve esse caso: os conectores dessas IAs também rodam na nuvem e não alcançam o `localhost`.

**A API não responde.** Rode `docker compose up -d` na pasta do Specboard e confira
http://localhost:8787/api/health.

## Para quem mexe no Specboard

O manual (`/llms.txt`), o prompt, as instruções do MCP e o roteiro do `/board` saem de
`backend/app/services/agent_docs.py`. Se mudar a API ou o texto, mude lá e regenere o `PROMPT.md` e o comando do
plugin (`integrations/claude-code/commands/board.md`); os testes `test_prompt_md_matches_default_prompt` e
`test_plugin_command_matches_board_prompt` acusam a diferença.
