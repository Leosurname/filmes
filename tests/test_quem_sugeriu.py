"""Quem sugeriu cada filme (issue #27)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.db as db  # noqa: E402
import app.main as main  # noqa: E402


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    banco = tmp_path / "teste.db"
    monkeypatch.setattr(db, "DB_PATH", banco)
    monkeypatch.setattr(main, "conectar", lambda: db.conectar(banco))
    contador = {"n": 0}

    def link_falso(url):
        contador["n"] += 1
        return {"imdb_id": f"tt{contador['n']}"}, None

    monkeypatch.setattr(main, "_dados_do_link", link_falso)
    with TestClient(main.app) as cliente:
        yield cliente


def entrar(cliente, nome):
    pessoa = cliente.post("/api/entrar", json={"nome": nome}).json()
    return pessoa, {"X-Pessoa-Id": str(pessoa["id"])}


def test_a_listagem_traz_o_nome_de_quem_sugeriu(cliente):
    _, cabecalho = entrar(cliente, "Maria")
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt1/"}, headers=cabecalho)

    filme = cliente.get("/api/filmes").json()[0]
    assert filme["sugerido_por"] == "Maria"
    assert filme["data_sugestao"]


def test_cada_filme_traz_a_sua_pessoa(cliente):
    _, do_leo = entrar(cliente, "Leo")
    _, da_maria = entrar(cliente, "Maria")
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt1/"}, headers=do_leo)
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt2/"}, headers=da_maria)

    por_nome = {f["imdb_id"]: f["sugerido_por"] for f in cliente.get("/api/filmes").json()}
    assert set(por_nome.values()) == {"Leo", "Maria"}


def test_o_nome_acompanha_a_correcao(cliente):
    _, cabecalho = entrar(cliente, "Lel")
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt1/"}, headers=cabecalho)
    cliente.patch("/api/pessoa", json={"nome": "Leo"}, headers=cabecalho)

    assert cliente.get("/api/filmes").json()[0]["sugerido_por"] == "Leo"


def test_filme_sem_pessoa_vinculada_nao_some(cliente):
    """Filme antigo, de antes da identificação, continua na lista."""
    conexao = db.conectar(db.DB_PATH)
    try:
        conexao.execute(
            "INSERT INTO filmes (url_original, imdb_id, status) VALUES (?, ?, ?)",
            ("https://imdb.com/title/tt99/", "tt99", "quero_ver"),
        )
        conexao.commit()
    finally:
        conexao.close()

    filmes = cliente.get("/api/filmes").json()
    assert len(filmes) == 1
    assert filmes[0]["pessoa_id"] is None
    assert filmes[0]["sugerido_por"] is None
