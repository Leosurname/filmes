"""API minima para suportar o filtro por tema (issue #12).

Nao implementa o fluxo completo de colar link + OMDb (issues #7/#8): o
endpoint de cadastro aqui recebe titulo e generos diretamente, so para
existir dado para filtrar e testar o filtro de tema.
"""

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.db import inserir_filme, init_db, listar_filmes, listar_generos

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Filmes da Familia")


@app.on_event("startup")
def _startup() -> None:
    init_db()


class NovoFilme(BaseModel):
    titulo: str
    generos: List[str] = []
    duracao_min: Optional[int] = None
    pessoa_nome: Optional[str] = None


@app.post("/api/filmes")
def criar_filme(filme: NovoFilme):
    novo_id = inserir_filme(
        titulo=filme.titulo,
        generos=filme.generos,
        duracao_min=filme.duracao_min,
        pessoa_nome=filme.pessoa_nome,
    )
    return {"id": novo_id}


@app.get("/api/filmes")
def obter_filmes(
    genero: Optional[List[str]] = Query(default=None),
    duracao_min: Optional[int] = None,
    duracao_max: Optional[int] = None,
    pessoa: Optional[str] = None,
):
    return listar_filmes(
        generos=genero,
        duracao_min=duracao_min,
        duracao_max=duracao_max,
        pessoa_nome=pessoa,
    )


@app.get("/api/generos")
def obter_generos():
    """Temas disponiveis para filtro: so os que existem em algum filme."""
    return listar_generos()


app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
