Quero que você mantenha meus projetos organizados usando o Specboard, um kanban spec-first que roda na minha máquina.

Endereço: http://localhost:8787

1. Leia agora o manual da API em http://localhost:8787/llms.txt (com curl ou sua ferramenta de requisição HTTP). Ele tem as regras e os endpoints.
2. Depois rode GET http://localhost:8787/api/briefing e me diga em poucas linhas o que está em andamento, o que travou e qual deve ser minha próxima prioridade.
3. Daqui pra frente, sem eu precisar pedir:
   - no começo de cada sessão de trabalho, consulte o briefing e me lembre das prioridades e dos lembretes que ele trouxer;
   - tudo que eu mencionar como tarefa, ideia, bug ou plano vira card no projeto certo (procure duplicata antes);
   - mova os cards conforme o trabalho anda (doing ao começar, done ao terminar, blocked se travar) e registre atividades curtas do que foi feito;
   - decisões e mudanças de escopo vão primeiro para a spec do projeto, depois viram cards;
   - sempre me mande o link do board ou do card que você criou ou mudou;
   - identifique-se com o header X-Actor (ex.: claude, chatgpt, gemini).
4. Se você tem memória persistente, salve estas regras e o endereço lá para seguir nas próximas conversas (Claude Code: ~/.claude/CLAUDE.md; Cursor: Rules; ChatGPT: Memória ou Instruções personalizadas; Gemini: Gem ou instruções salvas).
5. Se você não consegue fazer requisições HTTP, me avise e me passe os comandos curl prontos para eu rodar. Se a API não responder, peça para eu rodar `docker compose up -d` na pasta do Specboard.
