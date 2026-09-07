"""Criação do banco SQLite e queries usadas pela API.

Este módulo contém só o necessário para a feature de nota da família
(issue #19): schema completo das tabelas descritas no plan.md (para não
ficar incompatível com o que as outras issues vão precisar), e as
queries de leitura/gravação usadas pelas rotas de `main.py`.
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
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS pessoas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                data_entrada TEXT NOT NULL DEFAULT (datetime('now'))
            );

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
                pessoa_id INTEGER REFERENCES pessoas(id),
                data_sugestao TEXT NOT NULL DEFAULT (datetime('now')),
                status TEXT NOT NULL DEFAULT 'quero_ver',
                nota_familia REAL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def listar_filmes(status: str | None = None, ordenar: str | None = None) -> list[sqlite3.Row]:
    """Lista filmes, com filtro opcional por status e ordenação opcional.

    `ordenar` aceita apenas "nota_familia" por enquanto (é o que a issue #19
    pede). Outras ordenações ficam para a issue #14.
    """
    query = "SELECT * FROM filmes"
    params: list = []
    if status:
        query += " WHERE status = ?"
        params.append(status)

    if ordenar == "nota_familia":
        # NULLS LAST: filme sem nota da família ainda vai para o fim.
        query += " ORDER BY nota_familia IS NULL, nota_familia DESC"
    else:
        query += " ORDER BY id DESC"

    conn = get_connection()
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def buscar_filme(filme_id: int) -> sqlite3.Row | None:
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM filmes WHERE id = ?", (filme_id,)).fetchone()
    finally:
        conn.close()


def atualizar_nota_familia(filme_id: int, nota: float) -> sqlite3.Row | None:
    """Grava (ou troca) a nota da família de um filme já assistido.

    Retorna a linha atualizada, ou None se o filme não existe.
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE filmes SET nota_familia = ? WHERE id = ?",
            (nota, filme_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
        return conn.execute("SELECT * FROM filmes WHERE id = ?", (filme_id,)).fetchone()
    finally:
        conn.close()
