"""Criacao do banco SQLite e queries relacionadas a lista de filmes.

Escopo desta issue (#20): apenas o suficiente para separar a lista em duas
visoes ("quero_ver" e "assistido") e permitir filtrar por genero e duracao
nas duas. Campos de outras issues (pessoa que sugeriu, provedores, etc.) nao
fazem parte deste banco minimo.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "filmes.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS filmes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    ano INTEGER,
    duracao_min INTEGER,
    generos TEXT,
    classificacao TEXT,
    nota_imdb REAL,
    status TEXT NOT NULL DEFAULT 'quero_ver',
    data_sugestao TEXT,
    data_assistido TEXT,
    nota_familia REAL
);
"""

SEED = [
    # titulo, ano, duracao_min, generos, classificacao, nota_imdb, status, data_sugestao, data_assistido, nota_familia
    ("O Iluminado", 1980, 146, "Terror", "16", 8.4, "assistido", "2026-08-01", "2026-08-15", 9.0),
    ("Toy Story", 1995, 81, "Animação", "Livre", 8.3, "assistido", "2026-08-02", "2026-08-20", 9.5),
    ("Divertida Mente", 2015, 95, "Animação", "Livre", 8.1, "quero_ver", "2026-09-01", None, None),
    ("Um Lugar Silencioso", 2018, 90, "Terror", "14", 7.5, "quero_ver", "2026-09-02", None, None),
    ("A Forma da Água", 2017, 123, "Drama", "16", 7.3, "assistido", "2026-08-05", "2026-08-25", 7.0),
    ("Se Beber, Não Case!", 2009, 100, "Comédia", "16", 7.7, "quero_ver", "2026-09-03", None, None),
]


def conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco() -> None:
    conexao = conectar()
    try:
        conexao.execute(SCHEMA)
        conexao.commit()
        total = conexao.execute("SELECT COUNT(*) AS total FROM filmes").fetchone()["total"]
        if total == 0:
            conexao.executemany(
                """
                INSERT INTO filmes (
                    titulo, ano, duracao_min, generos, classificacao,
                    nota_imdb, status, data_sugestao, data_assistido, nota_familia
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                SEED,
            )
            conexao.commit()
    finally:
        conexao.close()


def listar_filmes(status: str, genero: str | None, duracao_max: int | None):
    query = "SELECT * FROM filmes WHERE status = ?"
    parametros: list = [status]

    if genero:
        query += " AND generos LIKE ?"
        parametros.append(f"%{genero}%")

    if duracao_max is not None:
        query += " AND duracao_min <= ?"
        parametros.append(duracao_max)

    query += " ORDER BY data_sugestao DESC"

    conexao = conectar()
    try:
        linhas = conexao.execute(query, parametros).fetchall()
        return [dict(linha) for linha in linhas]
    finally:
        conexao.close()


def listar_generos() -> list[str]:
    conexao = conectar()
    try:
        linhas = conexao.execute("SELECT DISTINCT generos FROM filmes").fetchall()
        return sorted({linha["generos"] for linha in linhas if linha["generos"]})
    finally:
        conexao.close()
