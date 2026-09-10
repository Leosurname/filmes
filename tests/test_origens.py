"""Front e servidor em endereços diferentes (issue #71)."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.db as db  # noqa: E402

PAGINA = "https://leosurname.github.io"


def montar_cliente(tmp_path, monkeypatch, origens):
    """Recarrega o app com FILMES_ORIGENS definida, já que ela é lida no import."""
    monkeypatch.setenv("FILMES_ORIGENS", origens)
    for modulo in ("app.main",):
        sys.modules.pop(modulo, None)
    import app.main as main  # noqa: PLC0415

    banco = tmp_path / "teste.db"
    monkeypatch.setattr(db, "DB_PATH", banco)
    monkeypatch.setattr(main, "conectar", lambda: db.conectar(banco))
    return TestClient(main.app)


def test_sem_configuracao_nenhuma_origem_externa_e_liberada(tmp_path, monkeypatch):
    with montar_cliente(tmp_path, monkeypatch, "") as cliente:
        resposta = cliente.get("/api/filmes", headers={"Origin": PAGINA})
        assert resposta.status_code == 200
        assert "access-control-allow-origin" not in resposta.headers


def test_origem_autorizada_recebe_permissao(tmp_path, monkeypatch):
    with montar_cliente(tmp_path, monkeypatch, PAGINA) as cliente:
        resposta = cliente.get("/api/filmes", headers={"Origin": PAGINA})
        assert resposta.headers.get("access-control-allow-origin") == PAGINA


def test_origem_nao_autorizada_nao_recebe_permissao(tmp_path, monkeypatch):
    with montar_cliente(tmp_path, monkeypatch, PAGINA) as cliente:
        resposta = cliente.get("/api/filmes", headers={"Origin": "https://site-estranho.com"})
        assert "access-control-allow-origin" not in resposta.headers


def test_o_header_de_identificacao_e_liberado(tmp_path, monkeypatch):
    """Sem isso o navegador barraria o X-Pessoa-Id e ninguém conseguiria enviar."""
    with montar_cliente(tmp_path, monkeypatch, PAGINA) as cliente:
        resposta = cliente.options(
            "/api/filmes",
            headers={
                "Origin": PAGINA,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-Pessoa-Id",
            },
        )
        assert "x-pessoa-id" in resposta.headers.get("access-control-allow-headers", "").lower()
