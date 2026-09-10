"""Quando o aparelho esquece a identificação (issue #33).

Acontece quando a pessoa limpa os dados do navegador, troca de celular ou abre
numa aba anônima. A identificação some, mas o histórico dela não pode sumir
junto — e digitar o mesmo nome tem que recuperar a mesma pessoa.
"""

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
        return {"imdb_id": f"tt{contador['n']}", "titulo": f"Filme {contador['n']}"}, None

    monkeypatch.setattr(main, "_dados_do_link", link_falso)
    with TestClient(main.app) as cliente:
        yield cliente


def entrar(cliente, nome):
    pessoa = cliente.post("/api/entrar", json={"nome": nome}).json()
    return pessoa, {"X-Pessoa-Id": str(pessoa["id"])}


def test_digitar_o_mesmo_nome_recupera_a_mesma_pessoa(cliente):
    antes, _ = entrar(cliente, "Leo")
    # O aparelho esqueceu: a pessoa entra de novo do zero.
    depois, _ = entrar(cliente, "Leo")
    assert depois["id"] == antes["id"]


def test_os_filmes_continuam_no_nome_dela(cliente):
    pessoa, cabecalho = entrar(cliente, "Leo")
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt1/"}, headers=cabecalho)
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt2/"}, headers=cabecalho)

    # Aparelho esqueceu, pessoa entra de novo.
    de_novo, _ = entrar(cliente, "Leo")

    filmes = cliente.get("/api/filmes").json()
    assert len(filmes) == 2
    assert all(filme["pessoa_id"] == de_novo["id"] for filme in filmes)


def test_entrar_de_novo_nao_cria_pessoa_duplicada(cliente):
    entrar(cliente, "Leo")
    entrar(cliente, "leo")
    entrar(cliente, " Leo ")

    conexao = db.conectar(db.DB_PATH)
    try:
        total = conexao.execute("SELECT count(*) AS n FROM pessoas").fetchone()["n"]
    finally:
        conexao.close()
    assert total == 1


def test_identificacao_perdida_pede_para_entrar_de_novo(cliente):
    """Sem identificação, a API recusa com mensagem que orienta a pessoa."""
    resposta = cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt1/"})
    assert resposta.status_code == 401
    assert "nome" in resposta.json()["detail"].lower()


def test_identificacao_de_pessoa_que_sumiu_nao_estoura(cliente):
    pessoa, cabecalho = entrar(cliente, "Leo")

    conexao = db.conectar(db.DB_PATH)
    try:
        conexao.execute("DELETE FROM pessoas WHERE id = ?", (pessoa["id"],))
        conexao.commit()
    finally:
        conexao.close()

    resposta = cliente.post(
        "/api/filmes", json={"url": "https://imdb.com/title/tt9/"}, headers=cabecalho
    )
    assert resposta.status_code == 401
    assert "de novo" in resposta.json()["detail"]
