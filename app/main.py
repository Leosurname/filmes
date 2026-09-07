"""API e servidor de arquivos estáticos.

Implementa só o necessário para a issue #18 (marcar filme como assistido):
listar filmes por status e alternar o status de um filme. As demais rotas
(cadastro de filme, filtros, metadados de OMDb/TMDB etc.) pertencem a outras
issues do plan.md.
"""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import db

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Filmes da Família")


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


class AtualizarStatusPayload(BaseModel):
    status: Literal["quero_ver", "assistido"]


@app.get("/api/filmes")
def listar_filmes(status: str = "quero_ver"):
    if status not in (db.STATUS_QUERO_VER, db.STATUS_ASSISTIDO):
        raise HTTPException(status_code=400, detail="status inválido")
    return db.listar_por_status(status)


@app.patch("/api/filmes/{filme_id}/status")
def atualizar_status_filme(filme_id: int, payload: AtualizarStatusPayload):
    filme = db.atualizar_status(filme_id, payload.status)
    if filme is None:
        raise HTTPException(status_code=404, detail="filme não encontrado")
    return filme


# Serve o front-end estático (index.html, style.css, app.js).
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
