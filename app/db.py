"""Acesso ao banco SQLite.

Este arquivo traz apenas os campos e as consultas necessarios para a
reconsulta periodica de provedores (issue #17). O schema completo da
tabela `filmes` (issue #2) pode acrescentar outras colunas depois; o
CREATE TABLE abaixo usa `IF NOT EXISTS` e as colunas aqui sao um
subconjunto minimo, entao convive bem com o restante do modelo descrito
no plan.md.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "filmes.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS filmes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                imdb_id TEXT,
                titulo TEXT,
                provedores TEXT,
                provedores_atualizado_em TEXT,
                status TEXT NOT NULL DEFAULT 'quero_ver'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def filmes_com_provedores_desatualizados(limite_iso: str) -> list[sqlite3.Row]:
    """Filmes ainda na fila (`quero_ver`) cujos provedores nunca foram
    buscados ou foram buscados antes de `limite_iso`."""
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT id, imdb_id, titulo
            FROM filmes
            WHERE status = 'quero_ver'
              AND imdb_id IS NOT NULL
              AND (provedores_atualizado_em IS NULL OR provedores_atualizado_em < ?)
            """,
            (limite_iso,),
        ).fetchall()
    finally:
        conn.close()


def atualizar_provedores(filme_id: int, provedores_json: str, atualizado_em: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE filmes SET provedores = ?, provedores_atualizado_em = ? WHERE id = ?",
            (provedores_json, atualizado_em, filme_id),
        )
        conn.commit()
    finally:
        conn.close()
