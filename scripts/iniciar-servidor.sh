#!/usr/bin/env bash
# Sobe o servidor do "Filmes da Família" acessível para toda a rede de casa.
#
# Usa --host 0.0.0.0 para aceitar conexões vindas de outros aparelhos na mesma
# rede Wi-Fi (celulares, tablets), não só da própria máquina.
#
# Sempre entra na pasta do projeto antes de rodar, para que o banco
# (filmes.db) fique sempre no mesmo lugar, não importa de onde o script
# foi chamado (terminal, atalho, LaunchAgent). Isso é o que garante que os
# dados sobrevivem a um reinício do servidor.

set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORTA:-8000}"

echo "Endereço local: http://$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "SEU-IP-LOCAL"):${PORT}"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
