"""Criação do banco SQLite e queries.

Escopo mínimo necessário para a issue #10 (avisar quando o filme já está na
lista). As colunas de metadados do filme (título, ano, duração, gênero...)
descritas no `plan.md` fazem parte das issues #2 e #8; aqui só criamos o que
é preciso para guardar o link, o imdb_id e quem sugeriu.
"""

import sqlite3
import unicodedata
from datetime import datetime, timezone
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
            CREATE TABLE IF NOT EXISTS pessoas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                nome_normalizado TEXT NOT NULL UNIQUE,
                data_entrada TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS filmes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_original TEXT NOT NULL,
                imdb_id TEXT NOT NULL UNIQUE,
                pessoa_id INTEGER NOT NULL REFERENCES pessoas(id),
                data_sugestao TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _normalizar_nome(nome: str) -> str:
    """Remove acentos e normaliza caixa para comparar nomes de pessoas.

    Garante o requisito do plan.md: "Nome com acento ou maiúscula diferente
    não pode criar pessoa duplicada".
    """
    nome = nome.strip().lower()
    sem_acento = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento


def get_or_create_pessoa(conn: sqlite3.Connection, nome: str) -> sqlite3.Row:
    nome = nome.strip()
    nome_normalizado = _normalizar_nome(nome)

    row = conn.execute(
        "SELECT * FROM pessoas WHERE nome_normalizado = ?", (nome_normalizado,)
    ).fetchone()
    if row:
        return row

    agora = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO pessoas (nome, nome_normalizado, data_entrada) VALUES (?, ?, ?)",
        (nome, nome_normalizado, agora),
    )
    conn.commit()
    return conn.execute(
        "SELECT * FROM pessoas WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()


def find_filme_by_imdb_id(conn: sqlite3.Connection, imdb_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT filmes.*, pessoas.nome AS pessoa_nome
        FROM filmes
        JOIN pessoas ON pessoas.id = filmes.pessoa_id
        WHERE filmes.imdb_id = ?
        """,
        (imdb_id,),
    ).fetchone()


def insert_filme(
    conn: sqlite3.Connection, url_original: str, imdb_id: str, pessoa_id: int
) -> sqlite3.Row:
    agora = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO filmes (url_original, imdb_id, pessoa_id, data_sugestao)
        VALUES (?, ?, ?, ?)
        """,
        (url_original, imdb_id, pessoa_id, agora),
    )
    conn.commit()
    return conn.execute(
        """
        SELECT filmes.*, pessoas.nome AS pessoa_nome
        FROM filmes
        JOIN pessoas ON pessoas.id = filmes.pessoa_id
        WHERE filmes.id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()


def list_filmes(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT filmes.*, pessoas.nome AS pessoa_nome
        FROM filmes
        JOIN pessoas ON pessoas.id = filmes.pessoa_id
        ORDER BY filmes.data_sugestao DESC
        """
    ).fetchall()
