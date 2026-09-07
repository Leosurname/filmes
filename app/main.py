"""
API minima para a issue #21 - Remover filme da lista.

Endpoints:
  GET    /api/filmes?status=quero_ver|assistido   -> lista filmes (sem filtro, lista todos)
  DELETE /api/filmes/{filme_id}                   -> remove um filme

Servir os arquivos estaticos do front-end tambem fica aqui, ja que ainda nao
existe estrutura de projeto definida por outra issue (#1).
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.db import get_connection, init_db

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Filmes da Familia")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/filmes")
def listar_filmes(status: str | None = None):
    conn = get_connection()
    try:
        if status:
            rows = conn.execute(
                "SELECT id, titulo, status, data_sugestao FROM filmes WHERE status = ? ORDER BY id DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, titulo, status, data_sugestao FROM filmes ORDER BY id DESC"
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@app.delete("/api/filmes/{filme_id}")
def remover_filme(filme_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM filmes WHERE id = ?", (filme_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Filme nao encontrado")
        conn.execute("DELETE FROM filmes WHERE id = ?", (filme_id,))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
