"""Criação do banco SQLite e queries relacionadas a filmes."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "filmes.db"

# Colunas da tabela `filmes`, na ordem definida em plan.md.
FILME_COLUNAS = [
    "id",
    "url_original",
    "imdb_id",
    "titulo",
    "ano",
    "duracao_min",
    "generos",
    "classificacao",
    "nota_imdb",
    "sinopse",
    "poster_url",
    "provedores",
    "pessoa_id",
    "data_sugestao",
    "status",
    "nota_familia",
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cria as tabelas do banco caso ainda não existam."""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pessoas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                data_entrada TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS filmes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_original TEXT,
                imdb_id TEXT,
                titulo TEXT,
                ano INTEGER,
                duracao_min INTEGER,
                generos TEXT,
                classificacao TEXT,
                nota_imdb REAL,
                sinopse TEXT,
                poster_url TEXT,
                provedores TEXT,
                pessoa_id INTEGER,
                data_sugestao TEXT,
                status TEXT,
                nota_familia REAL,
                FOREIGN KEY (pessoa_id) REFERENCES pessoas (id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def listar_filmes() -> list[dict]:
    """Devolve todos os filmes, ordenados dos mais recentes para os mais antigos.

    Devolve lista vazia (nunca levanta erro) quando não há filmes salvos.
    """
    conn = get_connection()
    try:
        linhas = conn.execute(
            "SELECT * FROM filmes ORDER BY datetime(data_sugestao) DESC, id DESC"
        ).fetchall()
        return [dict(linha) for linha in linhas]
    finally:
        conn.close()
