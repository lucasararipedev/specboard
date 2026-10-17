"""Instaladores do plugin do Claude Code, servidos pelo próprio Specboard: /install/claude-code.sh (Linux, macOS,
WSL, Git Bash) e /install/claude-code.ps1 (Windows, PowerShell).

Quem usa só a extensão do VS Code (ou do Cursor) não tem o comando `claude` no terminal: o binário fica dentro da
extensão. O script acha o Claude Code onde estiver e instala o plugin; se não achar, diz o que fazer.
"""

from ..config import Settings

MARKETPLACE = "lucasararipedev/specboard"
DEFAULT_URL = "http://localhost:8787"


def _notes(settings: Settings) -> list[str]:
    """Avisos do fim da instalação: endereço fora do padrão e token (nunca o valor do token)."""
    url = settings.public_url
    notes = []
    if url != DEFAULT_URL:
        notes.append(f"Seu Specboard está em {url}: defina SPECBOARD_URL={url} no ambiente para o plugin achar.")
    if settings.api_token:
        notes.append("Esta instância exige token: defina SPECBOARD_TOKEN no ambiente (o valor está no .env).")
    return notes


DONE = "Pronto. Abra um chat novo no Claude Code: na pasta de um projeto ele já começa ligado; nas outras, use /board."
MISSING = "Não achei o Claude Code nesta máquina."
INSTALL_HINT = "Instale o Claude Code (https://claude.com/claude-code) e rode este comando de novo,"
PALETTE_HINT = f"ou, no VS Code: paleta de comandos > Claude Code: Install Plugin > {MARKETPLACE}"


def claude_code_installer(settings: Settings) -> str:
    url = settings.public_url
    extra = "".join(f'echo "{note}"\n' for note in _notes(settings))
    return f"""#!/bin/sh
# Instala o plugin do Specboard no Claude Code (terminal, VS Code ou Cursor).
# Uso: curl -fsSL {url}/install/claude-code.sh | sh
set -e
MARKETPLACE="{MARKETPLACE}"

find_claude() {{
  if command -v claude >/dev/null 2>&1; then
    command -v claude
    return
  fi
  # A extensão traz o Claude Code dentro dela, fora do PATH. Procura da instalação mais recente para a mais antiga.
  for ext in $(ls -td "$HOME"/.vscode/extensions/anthropic.claude-code-* \\
    "$HOME"/.vscode-server/extensions/anthropic.claude-code-* \\
    "$HOME"/.vscode-insiders/extensions/anthropic.claude-code-* \\
    "$HOME"/.cursor/extensions/anthropic.claude-code-* \\
    "$HOME"/.cursor-server/extensions/anthropic.claude-code-* \\
    "$HOME"/.windsurf/extensions/anthropic.claude-code-* 2>/dev/null); do
    for bin in "$ext/resources/native-binary/claude" "$ext/resources/native-binary/claude.exe"; do
      if [ -x "$bin" ]; then
        echo "$bin"
        return
      fi
    done
  done
}}

CLAUDE=$(find_claude)
if [ -z "$CLAUDE" ]; then
  echo "{MISSING}" >&2
  echo "{INSTALL_HINT}" >&2
  echo "{PALETTE_HINT}" >&2
  exit 1
fi

echo "Claude Code: $CLAUDE"
"$CLAUDE" plugin install specboard --marketplace "$MARKETPLACE"
{extra}echo "{DONE}"
"""


def claude_code_installer_ps1(settings: Settings) -> str:
    """Mesma coisa para o Windows: `irm <url>/install/claude-code.ps1 | iex` no PowerShell."""
    url = settings.public_url
    extra = "".join(f"Write-Host '{note}'\n" for note in _notes(settings))
    return f"""# Instala o plugin do Specboard no Claude Code (terminal, VS Code ou Cursor), no Windows.
# Uso (PowerShell): irm {url}/install/claude-code.ps1 | iex
$ErrorActionPreference = 'Stop'
$marketplace = '{MARKETPLACE}'

$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $claude) {{
  # A extensão traz o Claude Code dentro dela, fora do PATH. Procura da instalação mais recente para a mais antiga.
  $dirs = '.vscode', '.vscode-insiders', '.cursor', '.windsurf' | ForEach-Object {{ Join-Path $HOME "$_/extensions" }}
  $claude = Get-ChildItem -Path $dirs -Directory -Filter 'anthropic.claude-code-*' -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    ForEach-Object {{ Join-Path $_.FullName 'resources/native-binary/claude.exe' }} |
    Where-Object {{ Test-Path $_ }} |
    Select-Object -First 1
}}

if (-not $claude) {{
  Write-Host '{MISSING}'
  Write-Host '{INSTALL_HINT}'
  Write-Host '{PALETTE_HINT}'
  return
}}

Write-Host "Claude Code: $claude"
& $claude plugin install specboard --marketplace $marketplace
{extra}Write-Host '{DONE}'
"""
