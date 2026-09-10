"""Testes do contrato de identificação entre aparelho e API (issue #31)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.db as db  # noqa: E402
import app.main as main  # noqa: E402

FILME = {"url": "https://www.imdb.com/title/tt0111161/"}


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    banco = tmp_path / "teste.db"
    monkeypatch.setattr(db, "DB_PATH", banco)
    monkeypatch.setattr(main, "conectar", lambda: db.conectar(banco))
    monkeypatch.setattr(main, "_dados_do_link", lambda url: ({"imdb_id": "tt1"}, None))
    with TestClient(main.app) as cliente:
        yield cliente


def test_entrar_devolve_id_e_nome(cliente):
    resposta = cliente.post("/api/entrar", json={"nome": "Leo"})
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Leo"
    assert isinstance(resposta.json()["id"], int)


def test_entrar_sem_nome_e_recusado(cliente):
    assert cliente.post("/api/entrar", json={"nome": "  "}).status_code == 400


def test_pedido_sem_identificacao_e_recusado_com_mensagem_clara(cliente):
    resposta = cliente.post("/api/filmes", json=FILME)
    assert resposta.status_code == 401
    assert "nome" in resposta.json()["detail"].lower()


def test_identificacao_desconhecida_nao_derruba_a_api(cliente):
    resposta = cliente.post("/api/filmes", json=FILME, headers={"X-Pessoa-Id": "9999"})
    assert resposta.status_code == 401
    assert "de novo" in resposta.json()["detail"]


def test_identificacao_sem_sentido_nao_derruba_a_api(cliente):
    resposta = cliente.post("/api/filmes", json=FILME, headers={"X-Pessoa-Id": "abc"})
    assert resposta.status_code == 401


def test_filme_fica_vinculado_a_quem_enviou(cliente):
    pessoa = cliente.post("/api/entrar", json={"nome": "Maria"}).json()
    resposta = cliente.post(
        "/api/filmes", json=FILME, headers={"X-Pessoa-Id": str(pessoa["id"])}
    )
    assert resposta.status_code == 201
    assert resposta.json()["pessoa_id"] == pessoa["id"]


def test_pessoa_id_do_corpo_do_pedido_e_ignorado(cliente):
    """Quem sugeriu vem da identificação, nunca de um campo que dá para forjar."""
    pessoa = cliente.post("/api/entrar", json={"nome": "Ana"}).json()
    resposta = cliente.post(
        "/api/filmes",
        json={**FILME, "pessoa_id": 999},
        headers={"X-Pessoa-Id": str(pessoa["id"])},
    )
    assert resposta.json()["pessoa_id"] == pessoa["id"]
