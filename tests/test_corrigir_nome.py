"""Correção do nome guardado no aparelho (issue #34)."""

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


def total_de_pessoas():
    conexao = db.conectar(db.DB_PATH)
    try:
        return conexao.execute("SELECT count(*) AS n FROM pessoas").fetchone()["n"]
    finally:
        conexao.close()


def test_corrigir_nao_cria_pessoa_nova(cliente):
    pessoa, cabecalho = entrar(cliente, "Lel")
    resposta = cliente.patch("/api/pessoa", json={"nome": "Leo"}, headers=cabecalho)

    assert resposta.status_code == 200
    assert resposta.json()["id"] == pessoa["id"]
    assert resposta.json()["nome"] == "Leo"
    assert total_de_pessoas() == 1


def test_os_filmes_continuam_com_a_pessoa(cliente):
    pessoa, cabecalho = entrar(cliente, "Lel")
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt1/"}, headers=cabecalho)
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt2/"}, headers=cabecalho)

    cliente.patch("/api/pessoa", json={"nome": "Leo"}, headers=cabecalho)

    filmes = cliente.get("/api/filmes").json()
    assert len(filmes) == 2
    assert all(filme["pessoa_id"] == pessoa["id"] for filme in filmes)


def test_a_identificacao_continua_valendo_depois_da_correcao(cliente):
    """Corrigir não pode fazer a tela de entrada voltar a aparecer."""
    _, cabecalho = entrar(cliente, "Lel")
    cliente.patch("/api/pessoa", json={"nome": "Leo"}, headers=cabecalho)

    resposta = cliente.post(
        "/api/filmes", json={"url": "https://imdb.com/title/tt3/"}, headers=cabecalho
    )
    assert resposta.status_code == 201


def test_corrigir_para_o_nome_de_outra_pessoa_e_recusado(cliente):
    entrar(cliente, "Maria")
    _, do_leo = entrar(cliente, "Leo")

    resposta = cliente.patch("/api/pessoa", json={"nome": "Maria"}, headers=do_leo)

    assert resposta.status_code == 409
    assert "Maria" in resposta.json()["detail"]
    assert total_de_pessoas() == 2


def test_ajustar_acento_do_proprio_nome_e_permitido(cliente):
    """"joao" -> "João" é a mesma pessoa: não pode bater no conflito de nome."""
    pessoa, cabecalho = entrar(cliente, "joao")
    resposta = cliente.patch("/api/pessoa", json={"nome": "João"}, headers=cabecalho)

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "João"
    assert resposta.json()["id"] == pessoa["id"]


def test_nome_vazio_e_recusado(cliente):
    _, cabecalho = entrar(cliente, "Leo")
    assert cliente.patch("/api/pessoa", json={"nome": "   "}, headers=cabecalho).status_code == 400


def test_corrigir_sem_identificacao_e_recusado(cliente):
    assert cliente.patch("/api/pessoa", json={"nome": "Leo"}).status_code == 401
