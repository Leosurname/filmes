"""Rotas da API e inicializacao do servidor.

Traz apenas o necessario para a issue #17 (reconsulta periodica e manual
de provedores). As demais rotas da API (salvar filme, listar, etc.) sao
escopo de outras issues (#3, #4, ...).
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI

from . import db, refresh_provedores

load_dotenv()

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    tarefa_periodica = asyncio.create_task(refresh_provedores.loop_periodico())
    try:
        yield
    finally:
        tarefa_periodica.cancel()


app = FastAPI(lifespan=lifespan)


@app.post("/api/filmes/atualizar-provedores")
async def disparar_atualizacao_provedores(background_tasks: BackgroundTasks):
    """Dispara na mao a reconsulta dos provedores dos filmes na fila.

    Responde na hora (nao espera a reconsulta terminar) - a atualizacao
    roda em segundo plano e nao trava quem esta usando a pagina.
    """
    background_tasks.add_task(refresh_provedores.atualizar_provedores_da_fila)
    return {"status": "disparado"}
