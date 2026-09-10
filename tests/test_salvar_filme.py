"""Testes do caminho principal: salvar um filme pelo link.

Existe por causa de uma regressão real: a função que busca os metadados foi
apagada por engano numa integração e o `POST /api/filmes` passou a estourar
`NameError`. O import continuava funcionando, então nada acusou. Estes testes
exercitam a rota de verdade.
"""

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
    with TestClient(main.app) as cliente:
        yield cliente


def cabecalho(cliente, nome="Leo"):
    pessoa = cliente.post("/api/entrar", json={"nome": nome}).json()
    return {"X-Pessoa-Id": str(pessoa["id"])}


def test_salvar_filme_responde_201(cliente):
    resposta = cliente.post("/api/filmes", json=FILME, headers=cabecalho(cliente))
    assert resposta.status_code == 201


def test_filme_salvo_aparece_na_listagem(cliente):
    cliente.post("/api/filmes", json=FILME, headers=cabecalho(cliente))
    assert len(cliente.get("/api/filmes").json()) == 1


def test_url_vazia_e_recusada(cliente):
    resposta = cliente.post("/api/filmes", json={"url": "   "}, headers=cabecalho(cliente))
    assert resposta.status_code == 400


def test_link_sem_filme_reconhecivel_ainda_salva(cliente):
    """Ninguém pode perder a indicação porque o link é estranho."""
    resposta = cliente.post(
        "/api/filmes", json={"url": "https://exemplo.com/nada"}, headers=cabecalho(cliente)
    )
    assert resposta.status_code == 201
    assert resposta.json()["aviso"]
