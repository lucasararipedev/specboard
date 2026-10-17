# Specboard para Claude Code

Liga o Claude Code ao seu [Specboard](https://github.com/lucasararipedev/specboard) (que precisa estar rodando,
por padrão em `http://localhost:8787`).

## Instalar

No terminal, com o Specboard no ar:

```bash
curl -fsSL http://localhost:8787/install/claude-code.sh | sh       # Linux, macOS, WSL, Git Bash
irm http://localhost:8787/install/claude-code.ps1 | iex            # Windows (PowerShell)
```

O instalador acha o Claude Code no terminal ou dentro da extensão do VS Code e do Cursor (que não põe o comando
`claude` no terminal) e roda `claude plugin install specboard --marketplace lucasararipedev/specboard`. Depois,
abra um chat novo.

## Comandos

| Comando | O que faz |
|---|---|
| `/board` | Liga este chat ao board, compara a conversa com o board, registra o que faltou (cards, status, decisões, perguntas, etiquetas) e responde em 3 linhas: **Registrei**, **Esquecendo**, **Agora**. |
| `/board off` | Desliga este chat: ele sai do painel Agora. |

Se outro plugin também tiver um `/board`, use `/specboard:board`.

## O que acontece sozinho

- **Ao abrir um chat** numa pasta que é o `repo` de um projeto do Specboard, o chat já começa ligado: aparece
  "Specboard ativo neste chat" e a IA recebe o briefing do projeto. Em outras pastas, fica desligado até o `/board`.
- **A cada resposta**, o chat ligado dá sinal de vida no painel **Agora** (`/projetos`); sem sinal há 15 min, aparece
  como parado.
- **Ao fechar o chat**, ele sai do painel.
- **Durante a conversa**, a IA usa as ferramentas do MCP (`/mcp`) para criar e mover cards, registrar decisões,
  perguntar o que só você sabe e atualizar o "fazendo agora".

## Configurar

| Variável de ambiente | Para quê |
|---|---|
| `SPECBOARD_URL` | Endereço do Specboard, se não for `http://localhost:8787` |
| `SPECBOARD_TOKEN` | Token, se a instância exige (`SPECBOARD_TOKEN` no `.env` do Specboard) |

Defina antes de abrir o Claude Code (ex.: no `~/.bashrc`).

## Atualizar e remover

```bash
claude plugin update specboard@specboard
claude plugin uninstall specboard@specboard
```

Sem o comando `claude` no terminal, use o caminho que o instalador mostrou na linha `Claude Code: …`.
