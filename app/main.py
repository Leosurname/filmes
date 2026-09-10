"""Rotas da API e servidor da aplicação Filmes da Família."""

import json
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import conectar, criar_schema, inserir_filme, listar_filmes
from app.pessoas import resolver as resolver_pessoa
from app.metadata import buscar_metadados, buscar_provedores, extract_imdb_id

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
    titulo: str | None = None
    metadados_encontrados: bool = True
    aviso: str | None = None


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
        pessoa_id = resolver_pessoa(conexao, nome)
        dados, aviso = _dados_do_link(url)

        # Duplicado se checa pelo imdb_id, nunca pela url: a mesma pessoa pode
        # colar links diferentes do mesmo filme.
        imdb_id = dados.get("imdb_id")
        if imdb_id:
            ja_existe = conexao.execute(
                "SELECT f.id, f.titulo, f.data_sugestao, p.nome "
                "FROM filmes f LEFT JOIN pessoas p ON p.id = f.pessoa_id "
                "WHERE f.imdb_id = ? ORDER BY f.id LIMIT 1",
                (imdb_id,),
            ).fetchone()
            if ja_existe is not None:
                quem = ja_existe["nome"] or "alguém da casa"
                titulo = ja_existe["titulo"] or "Esse filme"
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"{titulo} já está na lista: {quem} sugeriu "
                        f"em {ja_existe['data_sugestao']}."
                    ),
                )

        registro = {
            "url_original": url,
            "pessoa_id": pessoa_id,
            "data_sugestao": date.today().isoformat(),
            "status": "quero_ver",
        }
        registro.update(dados)
        filme_id = inserir_filme(conexao, registro)
        linha = conexao.execute(
            "SELECT id, url_original, pessoa_id, data_sugestao, status, titulo "
            "FROM filmes WHERE id = ?",
            (filme_id,),
        ).fetchone()
    finally:
        conexao.close()

    return FilmeResponse(
        **dict(linha),
        metadados_encontrados=aviso is None,
        aviso=aviso,
    )


class StatusRequest(BaseModel):
    status: str


@app.patch("/api/filmes/{filme_id}/status")
def mudar_status(filme_id: int, payload: StatusRequest) -> dict:
    """Move o filme entre `quero_ver` e `assistido`.

    Aceita os dois sentidos, então dá para desfazer se alguém clicar errado.
    """
    novo = (payload.status or "").strip()
    if novo not in ("quero_ver", "assistido"):
        raise HTTPException(
            status_code=400,
            detail="Status inválido. Use 'quero_ver' ou 'assistido'.",
        )

    conexao = conectar()
    try:
        atual = conexao.execute(
            "SELECT id FROM filmes WHERE id = ?", (filme_id,)
        ).fetchone()
        if atual is None:
            raise HTTPException(status_code=404, detail="Filme não encontrado.")

        data_assistido = date.today().isoformat() if novo == "assistido" else None
        conexao.execute(
            "UPDATE filmes SET status = ?, data_assistido = ? WHERE id = ?",
            (novo, data_assistido, filme_id),
        )
        conexao.commit()
        linha = conexao.execute(
            "SELECT id, status, data_assistido FROM filmes WHERE id = ?", (filme_id,)
        ).fetchone()
    finally:
        conexao.close()

    return dict(linha)


class NotaRequest(BaseModel):
    nota: float | None = None


@app.patch("/api/filmes/{filme_id}/nota")
def dar_nota(filme_id: int, payload: NotaRequest) -> dict:
    """Registra a nota que a família deu ao filme.

    A escala é de 0 a 10, a mesma do IMDb, para não confundir quem lê o card.
    Mandar `nota: null` apaga a nota.
    """
    nota = payload.nota
    if nota is not None and not (0 <= nota <= 10):
        raise HTTPException(status_code=400, detail="A nota vai de 0 a 10.")

    conexao = conectar()
    try:
        if conexao.execute("SELECT id FROM filmes WHERE id = ?", (filme_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Filme não encontrado.")
        conexao.execute(
            "UPDATE filmes SET nota_familia = ? WHERE id = ?", (nota, filme_id)
        )
        conexao.commit()
        linha = conexao.execute(
            "SELECT id, nota_imdb, nota_familia FROM filmes WHERE id = ?", (filme_id,)
        ).fetchone()
    finally:
        conexao.close()
    return dict(linha)


@app.delete("/api/filmes/{filme_id}", status_code=204)
def remover_filme(filme_id: int) -> None:
    """Apaga um filme da lista, em qualquer uma das duas visões."""
    conexao = conectar()
    try:
        if conexao.execute("SELECT id FROM filmes WHERE id = ?", (filme_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Filme não encontrado.")
        conexao.execute("DELETE FROM filmes WHERE id = ?", (filme_id,))
        conexao.commit()
    finally:
        conexao.close()


@app.post("/api/provedores/atualizar")
def atualizar_provedores(limite: int = 20) -> dict:
    """Reconsulta onde assistir os filmes que ainda estão na fila.

    Catálogo de streaming muda o tempo todo, então a informação envelhece
    sozinha. Reconsulta primeiro os que estão há mais tempo sem atualização.

    Só mexe em quem está em `quero_ver`: filme já assistido não precisa.
    """
    conexao = conectar()
    atualizados = 0
    try:
        linhas = conexao.execute(
            "SELECT id, imdb_id FROM filmes "
            "WHERE status = 'quero_ver' AND imdb_id IS NOT NULL "
            "ORDER BY provedores_atualizado_em IS NOT NULL, "
            "         provedores_atualizado_em ASC, id ASC "
            "LIMIT ?",
            (limite,),
        ).fetchall()

        for linha in linhas:
            try:
                provedores = buscar_provedores(linha["imdb_id"])
            except Exception:
                continue
            conexao.execute(
                "UPDATE filmes SET provedores = ?, provedores_atualizado_em = ? "
                "WHERE id = ?",
                (
                    json.dumps(provedores, ensure_ascii=False),
                    date.today().isoformat(),
                    linha["id"],
                ),
            )
            atualizados += 1
        conexao.commit()
    finally:
        conexao.close()

    return {"verificados": len(linhas), "atualizados": atualizados}


@app.get("/api/filmes")
def get_filmes() -> list[dict]:
    """Lista os filmes salvos, do mais recente para o mais antigo.

    Devolve todos os campos de cada filme e uma lista vazia — nunca um erro —
    quando ainda não há nada salvo.
    """
    conexao = conectar()
    try:
        return [dict(linha) for linha in listar_filmes(conexao)]
    finally:
        conexao.close()


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
