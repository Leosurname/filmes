"""Rotas da API e servidor.

Escopo mínimo para a issue #10 (avisar quando o filme já está na lista):
- POST /api/filmes: salva um filme a partir do link, checando duplicado
  pelo imdb_id. Se já existir, responde 409 com quem sugeriu e quando.
- GET /api/filmes: lista os filmes salvos.

A busca de metadados na OMDb/TMDB (título, ano, duração, pôster, onde
assistir...) e o tratamento completo de link inválido ficam para as
issues #7, #8 e #9.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import db
from app.metadata import extrair_imdb_id

app = FastAPI(title="Filmes da Família")


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


class NovoFilme(BaseModel):
    url: str
    nome: str


def _filme_para_json(row) -> dict:
    return {
        "id": row["id"],
        "url_original": row["url_original"],
        "imdb_id": row["imdb_id"],
        "sugerido_por": row["pessoa_nome"],
        "data_sugestao": row["data_sugestao"],
    }


@app.post("/api/filmes")
def criar_filme(payload: NovoFilme):
    nome = payload.nome.strip()
    if not nome:
        raise HTTPException(status_code=400, detail="Informe o seu nome.")

    imdb_id = extrair_imdb_id(payload.url)
    if not imdb_id:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível identificar o filme nesse link.",
        )

    conn = db.get_connection()
    try:
        existente = db.find_filme_by_imdb_id(conn, imdb_id)
        if existente:
            raise HTTPException(
                status_code=409,
                detail={
                    "mensagem": "Esse filme já está na lista.",
                    "filme": _filme_para_json(existente),
                },
            )

        pessoa = db.get_or_create_pessoa(conn, nome)
        filme = db.insert_filme(conn, payload.url.strip(), imdb_id, pessoa["id"])
        return _filme_para_json(filme)
    finally:
        conn.close()


@app.get("/api/filmes")
def listar_filmes():
    conn = db.get_connection()
    try:
        filmes = db.list_filmes(conn)
        return [_filme_para_json(f) for f in filmes]
    finally:
        conn.close()


app.mount("/", StaticFiles(directory="static", html=True), name="static")
