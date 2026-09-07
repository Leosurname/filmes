"""API e servidor estatico.

Escopo desta issue (#11): endpoint de listagem com filtro de faixa de
duracao. As demais rotas (salvar filme, login por nome, outros filtros)
pertencem a outras issues e nao sao implementadas aqui.
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from app.db import FAIXAS_DURACAO, init_db, listar_filmes

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Filmes da Familia")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/filmes")
def get_filmes(
    duracao: Optional[str] = Query(
        None,
        description="Faixa de duracao: ate_90, 90_120 ou mais_120",
    )
):
    if duracao is not None and duracao not in FAIXAS_DURACAO:
        raise HTTPException(
            status_code=400,
            detail=f"faixa de duracao invalida. Use uma de: {', '.join(FAIXAS_DURACAO)}",
        )

    filmes = listar_filmes(duracao=duracao)
    duracao_desconhecida = sum(1 for f in filmes if f["duracao_min"] is None)

    return {
        "filmes": filmes,
        "filtro_duracao": duracao,
        "filmes_duracao_desconhecida": duracao_desconhecida,
    }


app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
