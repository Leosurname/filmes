"""Rotas da API e servidor da aplicação Filmes da Família."""

from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import conectar, criar_schema, inserir_filme

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Garante que o banco e o schema existem antes de atender qualquer pedido."""
    conexao = conectar()
    try:
        criar_schema(conexao)
    finally:
        conexao.close()
    yield


app = FastAPI(title="Filmes da Família", lifespan=lifespan)


@app.get("/")
def index() -> FileResponse:
    """Serve a página inicial estática."""
    return FileResponse(STATIC_DIR / "index.html")


class NovoFilmeRequest(BaseModel):
    url: str = Field(default="")


class FilmeResponse(BaseModel):
    id: int
    url_original: str
    pessoa_id: int
    data_sugestao: str
    status: str


def _resolver_pessoa(conexao, nome: str) -> int:
    """Devolve o id da pessoa com esse nome, criando o registro se for a primeira vez.

    A comparação ignora maiúsculas e espaços nas pontas, para "Leo" e "leo "
    não virarem duas pessoas. O tratamento de acentos e o contrato definitivo
    de identificação são das issues #25 e #31, ainda não implementadas.
    """
    linha = conexao.execute(
        "SELECT id FROM pessoas WHERE lower(trim(nome)) = lower(trim(?))",
        (nome,),
    ).fetchone()
    if linha is not None:
        return linha["id"]

    cursor = conexao.execute(
        "INSERT INTO pessoas (nome, data_entrada) VALUES (?, ?)",
        (nome.strip(), date.today().isoformat()),
    )
    conexao.commit()
    return cursor.lastrowid


@app.post("/api/filmes", response_model=FilmeResponse, status_code=201)
def salvar_filme(
    payload: NovoFilmeRequest,
    x_pessoa_nome: str | None = Header(default=None),
) -> FilmeResponse:
    """Salva um filme a partir do link colado.

    Quem sugeriu não vem digitado no corpo do pedido: vem de quem está usando
    o sistema, pelo header `X-Pessoa-Nome`. Esse header é um contrato
    provisório — a issue #31 define o definitivo.
    """
    url = (payload.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="A url do filme é obrigatória.")

    nome = (x_pessoa_nome or "").strip()
    if not nome:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível identificar quem está enviando.",
        )

    conexao = conectar()
    try:
        pessoa_id = _resolver_pessoa(conexao, nome)
        filme_id = inserir_filme(
            conexao,
            {
                "url_original": url,
                "pessoa_id": pessoa_id,
                "data_sugestao": date.today().isoformat(),
                "status": "quero_ver",
            },
        )
        linha = conexao.execute(
            "SELECT id, url_original, pessoa_id, data_sugestao, status FROM filmes WHERE id = ?",
            (filme_id,),
        ).fetchone()
    finally:
        conexao.close()

    return FilmeResponse(**dict(linha))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
