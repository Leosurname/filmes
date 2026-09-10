"""Testes da identificação por nome (issue #25)."""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import criar_schema  # noqa: E402
from app.pessoas import buscar_por_id, normalizar, resolver  # noqa: E402


def conexao_em_memoria():
    conexao = sqlite3.connect(":memory:")
    conexao.row_factory = sqlite3.Row
    criar_schema(conexao)
    return conexao


def test_normalizar_tira_acento_caixa_e_espaco():
    assert normalizar("João") == "joao"
    assert normalizar("  JOÃO  ") == "joao"
    assert normalizar("Ana Maria") == "ana maria"
    assert normalizar("Ana   Maria") == "ana maria"
    assert normalizar("") == ""


def test_nome_novo_cria_pessoa():
    conexao = conexao_em_memoria()
    pessoa_id = resolver(conexao, "Leo")
    assert pessoa_id == 1
    assert buscar_por_id(conexao, pessoa_id)["nome"] == "Leo"


def test_mesmo_nome_reaproveita_a_pessoa():
    conexao = conexao_em_memoria()
    primeiro = resolver(conexao, "Leo")
    assert resolver(conexao, "Leo") == primeiro


def test_acento_e_caixa_diferentes_nao_duplicam():
    conexao = conexao_em_memoria()
    original = resolver(conexao, "João")
    for variacao in ["joao", "JOAO", " joão ", "JoÃo"]:
        assert resolver(conexao, variacao) == original

    total = conexao.execute("SELECT count(*) AS n FROM pessoas").fetchone()["n"]
    assert total == 1


def test_nomes_diferentes_sao_pessoas_diferentes():
    conexao = conexao_em_memoria()
    assert resolver(conexao, "Leo") != resolver(conexao, "Maria")


def test_o_nome_e_guardado_como_a_pessoa_escreveu():
    conexao = conexao_em_memoria()
    pessoa_id = resolver(conexao, "João")
    resolver(conexao, "joao")
    assert buscar_por_id(conexao, pessoa_id)["nome"] == "João"


def test_id_inexistente_devolve_none():
    assert buscar_por_id(conexao_em_memoria(), 999) is None
