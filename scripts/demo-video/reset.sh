#!/bin/sh
# Recria a instância de demo do zero (dados de exemplo, datas no passado).
set -e
cd "$(dirname "$0")"
docker rm -f specboard-demo >/dev/null 2>&1 || true
docker run -d --rm --name specboard-demo -p 127.0.0.1:8899:8787 -e SPECBOARD_PUBLIC_URL=http://localhost:8787 specboard:local >/dev/null
until curl -sf localhost:8899/api/health >/dev/null; do sleep 0.5; done
node seed.mjs >/dev/null
docker exec -i specboard-demo python - < backdate.py
echo reset ok
