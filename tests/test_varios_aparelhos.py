"""A mesma pessoa usando mais de um aparelho (issue #32).

O cenário: alguém usa o celular e também o notebook. Nos dois digita o mesmo
nome, e o sistema tem que entender que é a mesma pessoa — não duas.
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
        return {"imdb_id": f"tt{contador['n']}"}, None

    monkeypatch.setattr(main, "_dados_do_link", link_falso)
    with TestClient(main.app) as cliente:
        yield cliente


def entrar(cliente, nome):
    """Simula um aparelho entrando: devolve o header que ele passa a mandar."""
    pessoa = cliente.post("/api/entrar", json={"nome": nome}).json()
    return pessoa, {"X-Pessoa-Id": str(pessoa["id"])}


def test_mesmo_nome_em_outro_aparelho_e_a_mesma_pessoa(cliente):
    celular, _ = entrar(cliente, "Leo")
    notebook, _ = entrar(cliente, "Leo")
    assert celular["id"] == notebook["id"]


def test_acento_e_caixa_diferentes_entre_aparelhos_nao_duplicam(cliente):
    celular, _ = entrar(cliente, "João")
    notebook, _ = entrar(cliente, "joao")
    tablet, _ = entrar(cliente, " JOÃO ")
    assert celular["id"] == notebook["id"] == tablet["id"]


def test_sugestoes_dos_dois_aparelhos_ficam_sob_o_mesmo_nome(cliente):
    _, do_celular = entrar(cliente, "Leo")
    _, do_notebook = entrar(cliente, "Leo")

    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt1/"}, headers=do_celular)
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt2/"}, headers=do_notebook)

    filmes = cliente.get("/api/filmes").json()
    assert len(filmes) == 2
    assert len({filme["pessoa_id"] for filme in filmes}) == 1


def test_pessoas_diferentes_continuam_separadas(cliente):
    leo, do_leo = entrar(cliente, "Leo")
    maria, da_maria = entrar(cliente, "Maria")
    assert leo["id"] != maria["id"]

    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt1/"}, headers=do_leo)
    cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt2/"}, headers=da_maria)

    por_pessoa = {filme["pessoa_id"] for filme in cliente.get("/api/filmes").json()}
    assert por_pessoa == {leo["id"], maria["id"]}


def test_cada_aparelho_guarda_a_sua_identificacao(cliente):
    """O id devolvido é o mesmo, mas cada aparelho guarda a sua cópia.

    Entrar de novo não invalida o aparelho anterior: os dois continuam
    conseguindo enviar.
    """
    _, do_celular = entrar(cliente, "Leo")
    _, do_notebook = entrar(cliente, "Leo")

    primeiro = cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt1/"}, headers=do_celular)
    segundo = cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt2/"}, headers=do_notebook)
    terceiro = cliente.post("/api/filmes", json={"url": "https://imdb.com/title/tt3/"}, headers=do_celular)

    assert [primeiro.status_code, segundo.status_code, terceiro.status_code] == [201, 201, 201]
