"""Acesso ao banco SQLite.

Este modulo cria apenas o minimo de schema necessario para a issue #3
(salvar um filme a partir do link). O schema completo da tabela `filmes`
(com todos os campos de metadados e a tabela `pessoas`) e escopo da
issue #2 e da issue #25, e sera criado/expandido por elas.
"""

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("FILMES_DB_PATH", str(BASE_DIR / "filmes.db"))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Garante que a tabela `filmes` exista com as colunas usadas por esta issue.

    Colunas de metadados do filme (titulo, ano, generos, etc.) ficam para a
    issue #2 / #8, que vao evoluir esse schema.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS filmes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_original TEXT NOT NULL,
                quem_sugeriu TEXT NOT NULL,
                data_sugestao TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'quero_ver'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def inserir_filme(url_original: str, quem_sugeriu: str, data_sugestao: str, status: str = "quero_ver") -> sqlite3.Row:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO filmes (url_original, quem_sugeriu, data_sugestao, status)
            VALUES (?, ?, ?, ?)
            """,
            (url_original, quem_sugeriu, data_sugestao, status),
        )
        conn.commit()
        novo_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM filmes WHERE id = ?", (novo_id,)).fetchone()
        return row
    finally:
        conn.close()
