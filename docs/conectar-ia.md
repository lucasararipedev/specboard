# Conectar sua IA ao Specboard

O Specboard não tem IA dentro. Quem mantém o board é a IA que você já usa. Ela só precisa de duas coisas:
saber que o board existe (o prompt) e conseguir fazer requisições HTTP para `http://localhost:8787`.

A página **Conectar IA** da interface (http://localhost:8787/conectar) tem tudo isto com botão de copiar.

## O prompt padrão

Está em [PROMPT.md](../PROMPT.md) e em `http://localhost:8787/api/agent/prompt` (já com a URL e o aviso de token
da sua instância). Cole na IA uma vez. Ela lê o manual em `/llms.txt`, roda o briefing e passa a manter o board.

O manual (`/llms.txt`) é o que a IA consulta para saber as regras e os endpoints. Se mudar a API, mude ele também
(`backend/app/services/agent_docs.py`).

## Claude Code

Claude Code roda `curl` no terminal, então funciona direto.

**1. Memória permanente.** Cole no fim de `~/.claude/CLAUDE.md` (todos os repositórios) ou no `CLAUDE.md` de um
projeto:

```markdown
## Specboard (organização dos meus projetos)

- Kanban local em http://localhost:8787. Manual da API: http://localhost:8787/llms.txt (leia se ainda não leu nesta sessão).
- No início de cada sessão de trabalho, rode `curl -s http://localhost:8787/api/briefing` e me lembre das prioridades.
- Tarefas, ideias, bugs e planos que eu mencionar viram cards; mova o status conforme o trabalho anda e registre atividades curtas.
- Decisões e mudanças de escopo vão para a spec do projeto antes de virar card.
- Mande `X-Actor: claude` nas requisições e me passe o link do card ou do board quando mudar algo.
```

**2. Briefing automático no começo da sessão (opcional, mais forte).** Um hook `SessionStart` roda o briefing e
o resultado entra no contexto do Claude sozinho. Em `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "curl -sf --max-time 2 http://localhost:8787/api/briefing || true"
          }
        ]
      }
    ]
  }
}
```

O `|| true` evita erro quando o Specboard está desligado. Com token, acrescente
`-H "Authorization: Bearer SEU_TOKEN"`.

**3. Permissão.** Para o Claude não pedir confirmação a cada `curl`, libere com `/permissions` algo como
`Bash(curl *localhost:8787*)`, ou aprove na primeira vez com "não perguntar de novo".

## Cursor, Windsurf, GitHub Copilot

Cole o mesmo texto do item 1 nas Rules do projeto (ou nas User Rules para valer em tudo) ou num `AGENTS.md` na
raiz do repo. O agente precisa estar com acesso ao terminal liberado.

## Codex CLI, Gemini CLI, Aider, OpenCode

Use `AGENTS.md` (Codex, OpenCode), `GEMINI.md` (Gemini CLI) ou o arquivo de convenções do Aider com o texto do
item 1. Todos rodam `curl`.

## ChatGPT, Gemini e Claude no navegador

Eles rodam na nuvem e não alcançam o `localhost` da sua máquina. Duas saídas:

1. **Sem configurar nada:** cole o prompt. A IA vai te passar os comandos `curl` prontos e você roda no terminal
   (o prompt já pede isso). Funciona, mas dá mais trabalho.
2. **Expor com túnel:** suba um túnel HTTPS (ex.: `cloudflared tunnel --url http://localhost:8787`), defina
   `SPECBOARD_TOKEN` e `SPECBOARD_PUBLIC_URL` com a URL do túnel no `.env`, rode `docker compose up -d` de novo e
   use uma IA que consiga chamar URLs externas. **Nunca exponha sem token.**

Um servidor MCP para essas IAs está no roadmap ([spec.md](../spec.md), seção 7).

## Testando a conexão

Peça à IA: *"Crie um projeto no Specboard pro repositório atual, escreva uma spec curta e registre três
próximos passos."* Ela deve responder com o link do board, e os cards aparecem na interface em até 5 s.
