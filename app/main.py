"""API e servidor da lista de filmes da família.

Escopo desta issue (#20 - Visão dos filmes já assistidos): expõe as duas
visões da lista ("quero_ver" e "assistido"), com filtro por gênero e por
duração máxima funcionando em ambas, e serve o front-end estático.
"""

from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles

from app.db import inicializar_banco, listar_filmes, listar_generos

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Filmes da Família")


@app.on_event("startup")
def startup() -> None:
    inicializar_banco()


@app.get("/api/filmes")
def api_listar_filmes(
    status: Literal["quero_ver", "assistido"] = "quero_ver",
    genero: Optional[str] = Query(default=None),
    duracao_max: Optional[int] = Query(default=None, ge=0),
):
    return listar_filmes(status=status, genero=genero, duracao_max=duracao_max)


@app.get("/api/generos")
def api_listar_generos():
    return listar_generos()


app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
