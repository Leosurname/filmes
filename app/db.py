"""Criação do banco SQLite e queries usadas pela API.

Escopo desta issue (#9): o suficiente para salvar um filme (mesmo sem
metadados), listar e completar dados na mão depois. O schema completo de
`plan.md` (pessoas, provedores, status assistido etc.) é responsabilidade de
outras issues e será somado depois sem quebrar isto aqui.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "filmes.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS filmes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_original TEXT NOT NULL,
                imdb_id TEXT,
                titulo TEXT,
                ano INTEGER,
                duracao_min INTEGER,
                generos TEXT,
                classificacao TEXT,
                nota_imdb REAL,
                sinopse TEXT,
                poster_url TEXT,
                data_sugestao TEXT NOT NULL DEFAULT (datetime('now')),
                metadados_incompletos INTEGER NOT NULL DEFAULT 0,
                aviso_metadados TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
