"""Banco SQLite e queries relacionadas aos filmes.

Escopo desta issue (#12 - filtrar por tema): guardar os filmes com seus
generos e permitir listar filtrando por genero, combinando com outros
filtros que a lista de filmes venha a receber (ex.: duracao, pessoa).

Os demais recursos do `plan.md` (extrair link, OMDb, onde assistir,
classificacao, marcar como assistido etc.) sao de outras issues e nao
sao implementados aqui.
"""

import sqlite3
from pathlib import Path
from typing import Iterable, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "filmes.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS filmes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                generos TEXT NOT NULL DEFAULT '',
                duracao_min INTEGER,
                pessoa_nome TEXT
            )
            """
        )
        conn.commit()


def _normaliza_generos(generos: Iterable[str]) -> str:
    """Recebe generos e devolve string canonica 'Genero A, Genero B'."""
    limpos = []
    for g in generos:
        g = g.strip()
        if g and g not in limpos:
            limpos.append(g)
    return ", ".join(limpos)


def inserir_filme(
    titulo: str,
    generos: Iterable[str],
    duracao_min: Optional[int] = None,
    pessoa_nome: Optional[str] = None,
) -> int:
    generos_str = _normaliza_generos(generos)
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO filmes (titulo, generos, duracao_min, pessoa_nome) "
            "VALUES (?, ?, ?, ?)",
            (titulo, generos_str, duracao_min, pessoa_nome),
        )
        conn.commit()
        return cur.lastrowid


def _linha_para_dict(row: sqlite3.Row) -> dict:
    generos = [g.strip() for g in row["generos"].split(",") if g.strip()]
    return {
        "id": row["id"],
        "titulo": row["titulo"],
        "generos": generos,
        "duracao_min": row["duracao_min"],
        "pessoa_nome": row["pessoa_nome"],
    }


def listar_generos() -> list[str]:
    """So devolve generos que existem em algum filme cadastrado."""
    with get_connection() as conn:
        rows = conn.execute("SELECT generos FROM filmes").fetchall()
    encontrados: set[str] = set()
    for row in rows:
        for g in row["generos"].split(","):
            g = g.strip()
            if g:
                encontrados.add(g)
    return sorted(encontrados)


def listar_filmes(
    generos: Optional[list[str]] = None,
    duracao_min: Optional[int] = None,
    duracao_max: Optional[int] = None,
    pessoa_nome: Optional[str] = None,
) -> list[dict]:
    """Lista filmes, combinando (AND) os filtros informados.

    - `generos`: um filme aparece se tiver QUALQUER um dos generos pedidos
      (OR dentro do proprio filtro de tema), mas isso combina em AND com os
      demais filtros passados (duracao, pessoa etc.).
    """
    query = "SELECT * FROM filmes WHERE 1=1"
    params: list = []

    if generos:
        # filme com varios generos aparece se tiver pelo menos um dos
        # generos selecionados
        condicoes = []
        for g in generos:
            condicoes.append("(',' || REPLACE(generos, ', ', ',') || ',') LIKE ?")
            params.append(f"%,{g},%")
        query += " AND (" + " OR ".join(condicoes) + ")"

    if duracao_min is not None:
        query += " AND duracao_min IS NOT NULL AND duracao_min >= ?"
        params.append(duracao_min)

    if duracao_max is not None:
        query += " AND duracao_min IS NOT NULL AND duracao_min <= ?"
        params.append(duracao_max)

    if pessoa_nome:
        query += " AND pessoa_nome = ?"
        params.append(pessoa_nome)

    query += " ORDER BY id DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_linha_para_dict(r) for r in rows]
