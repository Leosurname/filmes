"""Acesso ao banco SQLite.

Escopo desta issue (#11 - filtro por faixa de duracao): fornece o minimo
necessario para guardar filmes e listar com filtro de duracao. Cadastro via
link (issues #3, #7, #8, #9, #10) e os demais filtros (issues #12, #13, #14)
ficam fora do escopo aqui.
"""

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "filmes.db"

# Faixas de duracao definidas no plan.md (Fase 3).
FAIXAS_DURACAO = {
    "ate_90": "duracao_min <= 90",
    "90_120": "duracao_min > 90 AND duracao_min <= 120",
    "mais_120": "duracao_min > 120",
}

# Dados de exemplo apenas para permitir testar o filtro manualmente, ja que
# o endpoint de cadastro (issue #3) ainda nao existe nesta branch.
FILMES_SEED = [
    ("Curta e Grossa", 82),
    ("Sessao da Tarde", 90),
    ("Equilibrio Perfeito", 105),
    ("Noite de Sexta", 118),
    ("Jornada Longa", 150),
    ("Epico Sem Fim", 205),
    ("Misterioso Sem Ficha", None),
    ("Achado no Grupo da Familia", None),
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS filmes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_original TEXT,
            imdb_id TEXT,
            titulo TEXT NOT NULL,
            ano INTEGER,
            duracao_min INTEGER,
            generos TEXT,
            classificacao TEXT,
            nota_imdb REAL,
            sinopse TEXT,
            poster_url TEXT,
            provedores TEXT,
            pessoa_id INTEGER,
            data_sugestao TEXT DEFAULT (date('now')),
            status TEXT DEFAULT 'quero_ver',
            nota_familia REAL
        )
        """
    )
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM filmes").fetchone()[0]
    if total == 0:
        conn.executemany(
            "INSERT INTO filmes (titulo, duracao_min) VALUES (?, ?)",
            FILMES_SEED,
        )
        conn.commit()

    conn.close()


def listar_filmes(duracao: Optional[str] = None) -> list[dict]:
    """Lista filmes, com filtro opcional de faixa de duracao.

    Um filme com `duracao_min` desconhecido (NULL) nunca eh removido pelo
    filtro de duracao: ele sempre aparece na lista, para nao sumir sem
    aviso. O front-end sinaliza esses casos com um aviso proprio.

    A condicao de duracao eh combinada por AND com quaisquer outros filtros
    que venham a existir (genero, classificacao, pessoa, etc.), entao esta
    funcao pode ganhar novos parametros opcionais sem quebrar o filtro de
    duracao.
    """
    if duracao is not None and duracao not in FAIXAS_DURACAO:
        raise ValueError(f"faixa de duracao invalida: {duracao}")

    condicoes = []
    if duracao is not None:
        condicoes.append(f"(duracao_min IS NULL OR ({FAIXAS_DURACAO[duracao]}))")

    sql = "SELECT * FROM filmes"
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY (duracao_min IS NULL), duracao_min"

    conn = get_connection()
    linhas = conn.execute(sql).fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]
