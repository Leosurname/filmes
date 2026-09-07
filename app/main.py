"""Rotas da API e ponto de entrada do servidor."""

from fastapi import FastAPI

from app.db import init_db, listar_filmes

app = FastAPI(title="Filmes da Família")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/filmes")
def get_filmes() -> list[dict]:
    """Lista todos os filmes salvos, com todos os campos, do mais recente
    para o mais antigo. Devolve lista vazia quando ainda não há filmes."""
    return listar_filmes()
