"""Rotas da API e servidor da aplicação Filmes da Família."""

import json
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import conectar, criar_schema, inserir_filme, listar_filmes
from app.pessoas import NomeJaUsado, buscar_por_id, renomear, resolver as resolver_pessoa
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


# --- Contrato de identificacao ---------------------------------------------
#
# A casa nao tem senha. O que identifica quem esta usando e o id da pessoa,
# que o aparelho guarda depois de entrar uma vez.
#
# 1. Na primeira visita o aparelho chama POST /api/entrar com o nome digitado
#    e recebe de volta {id, nome}.
# 2. Dali em diante, todo pedido que cria ou altera algo manda esse id no
#    header X-Pessoa-Id.
#
# Pedido sem identificacao e recusado com mensagem clara, e id que nao existe
# mais nao derruba a API: devolve 401 pedindo para entrar de novo, e o
# aparelho sabe que precisa mostrar a tela de entrada outra vez.


class EntrarRequest(BaseModel):
    nome: str = ""


class PessoaResponse(BaseModel):
    id: int
    nome: str


@app.post("/api/entrar", response_model=PessoaResponse)
def entrar(payload: EntrarRequest) -> PessoaResponse:
    """Identifica a pessoa pelo nome digitado e devolve o id que o aparelho guarda.

    Não é login com senha: é só dizer quem você é. Nome que já existe devolve a
    mesma pessoa, então entrar de novo — em outro aparelho ou depois de limpar
    os dados — recupera o histórico.
    """
    nome = " ".join((payload.nome or "").split())
    if not nome:
        raise HTTPException(status_code=400, detail="Digite o seu nome para entrar.")

    conexao = conectar()
    try:
        pessoa_id = resolver_pessoa(conexao, nome)
        pessoa = buscar_por_id(conexao, pessoa_id)
    finally:
        conexao.close()

    return PessoaResponse(id=pessoa["id"], nome=pessoa["nome"])


def pessoa_do_pedido(x_pessoa_id: str | None = Header(default=None)) -> int:
    """Descobre de quem é o pedido, a partir do id guardado no aparelho.

    Recusa o pedido quando não vem identificação, e também quando o id aponta
    para alguém que não existe mais — nesse caso sem estourar erro interno.
    """
    bruto = (x_pessoa_id or "").strip()
    if not bruto:
        raise HTTPException(
            status_code=401,
            detail="Não sabemos quem está enviando. Entre com o seu nome.",
        )

    try:
        pessoa_id = int(bruto)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Identificação inválida. Entre com o seu nome de novo.",
        )

    conexao = conectar()
    try:
        pessoa = buscar_por_id(conexao, pessoa_id)
    finally:
        conexao.close()

    if pessoa is None:
        raise HTTPException(
            status_code=401,
            detail="Essa identificação não vale mais. Entre com o seu nome de novo.",
        )

    return pessoa["id"]


@app.patch("/api/pessoa", response_model=PessoaResponse)
def corrigir_nome(
    payload: EntrarRequest,
    pessoa_id: int = Depends(pessoa_do_pedido),
) -> PessoaResponse:
    """Corrige o nome de quem está usando o aparelho.

    Quem digitou errado na primeira visita ficaria preso àquele nome, porque o
    sistema não pergunta de novo. Isto renomeia a pessoa que já existe: os
    filmes que ela sugeriu continuam com ela, agora com o nome certo.
    """
    nome = " ".join((payload.nome or "").split())
    if not nome:
        raise HTTPException(status_code=400, detail="Digite o nome corrigido.")

    conexao = conectar()
    try:
        try:
            renomear(conexao, pessoa_id, nome)
        except NomeJaUsado:
            raise HTTPException(
                status_code=409,
                detail=f"Já existe alguém na casa como {nome}.",
            )
        pessoa = buscar_por_id(conexao, pessoa_id)
    finally:
        conexao.close()

    return PessoaResponse(id=pessoa["id"], nome=pessoa["nome"])


def _dados_do_link(url: str) -> tuple[dict, str | None]:
    """Descobre o que der sobre o filme a partir do link.

    Nunca levanta erro: se o link não for identificável, se a OMDb não achar o
    filme ou se a rede falhar, devolve o que conseguiu e um aviso para a
    pessoa. A sugestão é salva de qualquer jeito — ninguém perde a indicação.
    """
    imdb_id = extract_imdb_id(url)
    if not imdb_id:
        return {}, (
            "Não deu para identificar o filme por esse link. "
            "Ele foi salvo assim mesmo, e os dados podem ser preenchidos depois."
        )

    dados: dict = {"imdb_id": imdb_id}

    try:
        metadados = buscar_metadados(imdb_id)
    except Exception:
        metadados = None

    if not metadados:
        return dados, (
            "O filme foi salvo, mas não achamos os dados dele agora. "
            "Dá para tentar de novo mais tarde."
        )

    dados.update(
        {
            "titulo": metadados.get("titulo"),
            "ano": metadados.get("ano"),
            "duracao_min": metadados.get("duracao_min"),
            "generos": metadados.get("generos"),
            "classificacao": metadados.get("classificacao"),
            "nota_imdb": metadados.get("nota_imdb"),
            "sinopse": metadados.get("sinopse"),
        }
    )

    try:
        provedores = buscar_provedores(imdb_id)
        if provedores:
            dados["provedores"] = json.dumps(provedores, ensure_ascii=False)
    except Exception:
        pass

    return dados, None


@app.post("/api/filmes", response_model=FilmeResponse, status_code=201)
def salvar_filme(
    payload: NovoFilmeRequest,
    pessoa_id: int = Depends(pessoa_do_pedido),
) -> FilmeResponse:
    """Salva um filme a partir do link colado.

    Quem sugeriu não vem no corpo do pedido: vem de quem está usando o sistema,
    pelo id que o aparelho guardou ao entrar (ver o contrato acima).
    """
    url = (payload.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="A url do filme é obrigatória.")

    conexao = conectar()
    try:
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
