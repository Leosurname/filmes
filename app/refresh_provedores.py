"""Reconsulta periodica de provedores dos filmes na fila (issue #17).

- Filme com dados antigos e reconsultado (ver `HORAS_PARA_CONSIDERAR_ANTIGO`).
- Roda em background (task assincrona / BackgroundTasks do FastAPI), entao
  nao trava a pagina de quem esta usando.
- Pode ser disparada na mao via POST /api/filmes/atualizar-provedores.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

from . import db, providers

logger = logging.getLogger("app.refresh_provedores")

HORAS_PARA_CONSIDERAR_ANTIGO = 24
INTERVALO_ENTRE_CICLOS_SEGUNDOS = 60 * 60

_atualizacao_em_andamento = asyncio.Lock()


async def atualizar_provedores_da_fila() -> int:
    """Reconsulta os filmes da fila com provedores desatualizados.

    Retorna quantos filmes foram atualizados. Se ja houver uma atualizacao
    rodando, apenas retorna sem fazer nada (evita reconsultas duplicadas).
    """
    if _atualizacao_em_andamento.locked():
        logger.info("Atualizacao de provedores ja em andamento; ignorando novo disparo")
        return 0

    async with _atualizacao_em_andamento:
        limite = datetime.now(timezone.utc) - timedelta(hours=HORAS_PARA_CONSIDERAR_ANTIGO)
        filmes = db.filmes_com_provedores_desatualizados(limite.isoformat())

        atualizados = 0
        for filme in filmes:
            try:
                provedores = await asyncio.to_thread(providers.buscar_provedores_tmdb, filme["imdb_id"])
            except Exception:
                logger.exception("Falha inesperada ao reconsultar filme %s", filme["id"])
                continue

            if provedores is None:
                continue

            agora = datetime.now(timezone.utc).isoformat()
            db.atualizar_provedores(filme["id"], json.dumps(provedores, ensure_ascii=False), agora)
            atualizados += 1

            # Cede o loop de eventos entre um filme e outro para nao
            # segurar o servidor enquanto reconsulta varios filmes.
            await asyncio.sleep(0)

        logger.info("Reconsulta de provedores concluida: %s/%s filmes atualizados", atualizados, len(filmes))
        return atualizados


async def loop_periodico() -> None:
    """Dispara a reconsulta de tempos em tempos, sozinho, sem intervencao."""
    while True:
        await asyncio.sleep(INTERVALO_ENTRE_CICLOS_SEGUNDOS)
        try:
            await atualizar_provedores_da_fila()
        except Exception:
            logger.exception("Falha no ciclo periodico de reconsulta de provedores")
