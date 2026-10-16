# Vídeo de demonstração

Grava o vídeo da página inicial (`frontend/public/demo.mp4`, `demo.webm` e `demo-poster.jpg`) e o GIF do
README (`docs/demo.gif`): um navegador
automatizado usa o Specboard com cursor, zoom e legendas, e a "IA" mexe no board pela API no meio do caminho.

Roda numa instância descartável na porta 8899, com dados de exemplo (`seed.mjs`), sem tocar nos seus projetos.

```bash
make up                                   # builda a imagem specboard:local com o front atual
cd scripts/demo-video
npm install && npx playwright install chromium
npm run build                             # reset + gravação + montagem + cópia para frontend/public
docker rm -f specboard-demo               # desliga a instância de demo
```

- `record.mjs` é o roteiro (cenas, legendas, zooms). Mudou a interface? Ajuste os seletores lá.
- `assemble.mjs` junta os quadros; `SPEED=1.3` acelera, e as esperas do polling de 5 s são cortadas.
