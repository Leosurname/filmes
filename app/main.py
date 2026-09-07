"""API do Filmes da Familia.

Este modulo implementa, por enquanto, apenas o `POST /api/filmes` (issue #3).

Mudanca de escopo (comentario da issue #3): com a identificacao por nome
(issue #25), o `quem_sugeriu` NAO vem mais digitado no corpo do pedido.
Ele vem de quem esta usando o sistema. Como o mecanismo de identificacao do
aparelho ainda nao existe (issues #25/#30/#31), este endpoint le a pessoa a
partir do header `X-Pessoa-Nome`, que e o contrato mais simples possivel para
o front-end enviar "quem esta logado" em cada chamada. Quando a issue #31
definir a forma definitiva de identificacao do aparelho, este ponto deve ser
ajustado para usar o mecanismo oficial.
"""

from datetime import date

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.db import inserir_filme, init_db

app = FastAPI(title="Filmes da Familia")


@app.on_event("startup")
def _on_startup() -> None:
    init_db()


class NovoFilmeRequest(BaseModel):
    url: str = Field(default="")


class FilmeResponse(BaseModel):
    id: int
    url_original: str
    quem_sugeriu: str
    data_sugestao: str
    status: str


@app.post("/api/filmes", response_model=FilmeResponse, status_code=201)
def salvar_filme(
    payload: NovoFilmeRequest,
    x_pessoa_nome: str | None = Header(default=None),
) -> FilmeResponse:
    url = (payload.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="A url do filme e obrigatoria.")

    quem_sugeriu = (x_pessoa_nome or "").strip()
    if not quem_sugeriu:
        raise HTTPException(
            status_code=400,
            detail="Nao foi possivel identificar quem esta enviando (header X-Pessoa-Nome ausente).",
        )

    row = inserir_filme(
        url_original=url,
        quem_sugeriu=quem_sugeriu,
        data_sugestao=date.today().isoformat(),
        status="quero_ver",
    )

    return FilmeResponse(
        id=row["id"],
        url_original=row["url_original"],
        quem_sugeriu=row["quem_sugeriu"],
        data_sugestao=row["data_sugestao"],
        status=row["status"],
    )
