---
description: Liga este chat ao Specboard, sincroniza a conversa com o board e mostra o status em 3 linhas
argument-hint: "[off]"
---
Specboard: sincronize esta conversa com o board e me dê um status curto.

Argumento: $ARGUMENTS

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
