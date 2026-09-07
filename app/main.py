"""Rotas da API e servidor estático.

Implementação mínima para a issue #19 (Dar a nota da família): expõe a
listagem de filmes (com filtro por status e ordenação pela nota da família)
e o endpoint que grava/troca essa nota. Não implementa as outras rotas do
plan.md (cadastro de filme a partir de link, filtros de duração/tema/etc,
login por nome...) — isso é escopo de outras issues.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import db

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Filmes da Família")


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


class NotaFamiliaEntrada(BaseModel):
    nota_familia: float = Field(ge=0, le=10)


def _filme_para_json(row) -> dict:
    return {
        "id": row["id"],
        "titulo": row["titulo"],
        "ano": row["ano"],
        "poster_url": row["poster_url"],
        "status": row["status"],
        "nota_imdb": row["nota_imdb"],
        "nota_familia": row["nota_familia"],
        "data_sugestao": row["data_sugestao"],
    }


@app.get("/api/filmes")
def get_filmes(status: str | None = None, ordenar: str | None = None):
    rows = db.listar_filmes(status=status, ordenar=ordenar)
    return [_filme_para_json(row) for row in rows]


@app.put("/api/filmes/{filme_id}/nota-familia")
def put_nota_familia(filme_id: int, entrada: NotaFamiliaEntrada):
    filme = db.buscar_filme(filme_id)
    if filme is None:
        raise HTTPException(status_code=404, detail="Filme não encontrado")
    if filme["status"] != "assistido":
        raise HTTPException(
            status_code=400,
            detail="Só dá para dar nota da família depois de marcar o filme como assistido",
        )

    row = db.atualizar_nota_familia(filme_id, entrada.nota_familia)
    return _filme_para_json(row)


# Serve o front-end estático (deixado por último para não sombrear /api/*).
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
