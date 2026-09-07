"""
Banco SQLite para a lista de filmes.

Escopo desta issue (#21 - Remover filme da lista): apenas o suficiente para
listar filmes por visao (quero_ver / assistido) e apagar um filme.

As demais colunas do modelo de dados completo (ver plan.md) e os fluxos de
adicionar filme via link, enriquecimento com OMDb/TMDB, filtros etc. sao
escopo de outras issues (#1, #2, #3, #5, #6, ...) e nao sao implementados aqui.
Para permitir testar a remocao sem depender dessas issues, o banco e
semeado com alguns filmes de exemplo na primeira execucao.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "filmes.db"

SEED_FILMES = [
    ("O Poderoso Chefao", "quero_ver"),
    ("Toy Story", "quero_ver"),
    ("Matrix", "assistido"),
    ("Divertida Mente", "assistido"),
]


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
                titulo TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'quero_ver',
                data_sugestao TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()

        (count,) = conn.execute("SELECT COUNT(*) FROM filmes").fetchone()
        if count == 0:
            conn.executemany(
                "INSERT INTO filmes (titulo, status) VALUES (?, ?)",
                SEED_FILMES,
            )
            conn.commit()
    finally:
        conn.close()
