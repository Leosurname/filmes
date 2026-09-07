"""Banco SQLite da lista de filmes.

Este modulo so cria o minimo da tabela `filmes` (conforme o `plan.md`)
necessario para a issue #13 (filtro por classificacao indicativa). As
demais colunas e funcionalidades (buscar na OMDb, salvar filme a partir de
link, onde assistir, etc.) pertencem a outras issues e nao sao tratadas
aqui.
"""

import os
import sqlite3

CAMINHO_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "filmes.db")


def conectar():
    conexao = sqlite3.connect(CAMINHO_DB)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_schema(conexao):
    conexao.execute(
        """
        CREATE TABLE IF NOT EXISTS filmes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            ano INTEGER,
            classificacao TEXT
        )
        """
    )
    conexao.commit()


_FILMES_EXEMPLO = [
    # (titulo, ano, classificacao no padrao OMDb)
    ("Toy Story", 1995, "G"),
    ("Homem-Aranha: Sem Volta Para Casa", 2021, "PG-13"),
    ("Divertida Mente", 2015, "PG"),
    ("Duro de Matar", 1988, "R"),
    ("O Iluminado", 1980, "R"),
    ("Vingadores: Ultimato", 2019, "PG-13"),
    ("Documentario Sem Classificacao", 2020, "N/A"),
]


def seed_dados_exemplo(conexao):
    """Popula o banco com alguns filmes de exemplo, se ele estiver vazio.

    Serve apenas para permitir testar o filtro de classificacao antes de a
    issue de buscar dados na OMDb (issue #8) e a de salvar filme a partir de
    link (issue #3) existirem.
    """
    total = conexao.execute("SELECT COUNT(*) AS n FROM filmes").fetchone()["n"]
    if total > 0:
        return
    conexao.executemany(
        "INSERT INTO filmes (titulo, ano, classificacao) VALUES (?, ?, ?)",
        _FILMES_EXEMPLO,
    )
    conexao.commit()


def listar_filmes(conexao):
    linhas = conexao.execute(
        "SELECT id, titulo, ano, classificacao FROM filmes ORDER BY titulo"
    ).fetchall()
    return [dict(linha) for linha in linhas]


def inicializar():
    conexao = conectar()
    try:
        criar_schema(conexao)
        seed_dados_exemplo(conexao)
    finally:
        conexao.close()
