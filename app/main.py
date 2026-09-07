"""API e servidor de arquivos estáticos.

Escopo desta issue (#9) — tratar link inválido e filme não encontrado:
- POST /api/filmes salva o filme mesmo quando a busca de metadados falha,
  e nunca deixa uma exceção de rede derrubar a resposta.
- GET /api/filmes lista os filmes salvos, incompletos ou não.
- PATCH /api/filmes/{id} deixa completar os dados na mão depois.

Outros endpoints (pessoas, filtros, "onde assistir" etc.) pertencem a
outras issues e não são criados aqui.
"""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import db
from .metadata import buscar_metadados

load_dotenv()

app = FastAPI(title="Filmes da Família")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


class NovoFilme(BaseModel):
    url: str


class AtualizarFilme(BaseModel):
    titulo: Optional[str] = None
    ano: Optional[int] = None
    duracao_min: Optional[int] = None
    generos: Optional[str] = None
    classificacao: Optional[str] = None
    nota_imdb: Optional[float] = None
    sinopse: Optional[str] = None
    poster_url: Optional[str] = None


def _row_to_dict(row) -> dict:
    filme = dict(row)
    filme["metadados_incompletos"] = bool(filme["metadados_incompletos"])
    return filme


@app.post("/api/filmes", status_code=201)
def criar_filme(novo: NovoFilme):
    url = (novo.url or "").strip()
    if not url:
        raise HTTPException(status_code=422, detail="Envie um link para o filme.")

    # buscar_metadados nunca lança exceção: uma API externa fora do ar,
    # um link sem id reconhecível ou um filme não encontrado sempre voltam
    # como um resultado incompleto com aviso, nunca como erro 500.
    resultado = buscar_metadados(url)

    conn = db.get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO filmes (
                url_original, imdb_id, titulo, ano, duracao_min, generos,
                classificacao, nota_imdb, sinopse, poster_url,
                metadados_incompletos, aviso_metadados
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                url,
                resultado.imdb_id,
                resultado.titulo,
                resultado.ano,
                resultado.duracao_min,
                resultado.generos,
                resultado.classificacao,
                resultado.nota_imdb,
                resultado.sinopse,
                resultado.poster_url,
                1 if resultado.incompleto else 0,
                resultado.aviso,
            ),
        )
        conn.commit()
        filme_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM filmes WHERE id = ?", (filme_id,)).fetchone()
    finally:
        conn.close()

    return _row_to_dict(row)


@app.get("/api/filmes")
def listar_filmes():
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM filmes ORDER BY data_sugestao DESC"
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_dict(row) for row in rows]


@app.patch("/api/filmes/{filme_id}")
def atualizar_filme(filme_id: int, dados: AtualizarFilme):
    campos = {k: v for k, v in dados.model_dump().items() if v is not None}
    if not campos:
        raise HTTPException(status_code=422, detail="Nenhum dado para atualizar.")

    conn = db.get_connection()
    try:
        existente = conn.execute(
            "SELECT * FROM filmes WHERE id = ?", (filme_id,)
        ).fetchone()
        if existente is None:
            raise HTTPException(status_code=404, detail="Filme não encontrado.")

        colunas = ", ".join(f"{campo} = ?" for campo in campos)
        valores = list(campos.values())

        # Depois de completar os dados na mão, o filme deixa de estar
        # marcado como incompleto.
        conn.execute(
            f"UPDATE filmes SET {colunas}, metadados_incompletos = 0, "
            "aviso_metadados = NULL WHERE id = ?",
            (*valores, filme_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM filmes WHERE id = ?", (filme_id,)).fetchone()
    finally:
        conn.close()

    return _row_to_dict(row)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
