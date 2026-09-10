"""Conexao com o SQLite e schema das tabelas `pessoas` e `filmes`.

Cobre a Issue #2 (Fase 1 do plan.md): criar o banco, criar a tabela e
oferecer funcoes basicas de inserir e listar filmes.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

# Caminho do banco na raiz do projeto (ao lado da pasta app/).
DB_PATH = Path(__file__).resolve().parent.parent / "filmes.db"

CRIAR_TABELA_PESSOAS = """
CREATE TABLE IF NOT EXISTS pessoas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    data_entrada TEXT NOT NULL
);
"""

CRIAR_TABELA_FILMES = """
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
    provedores_atualizado_em TEXT,
    pessoa_id INTEGER,
    data_sugestao TEXT,
    status TEXT,
    data_assistido TEXT,
    nota_familia REAL,
    FOREIGN KEY (pessoa_id) REFERENCES pessoas (id)
);
"""

# Colunas na mesma ordem usada por inserir_filme / listar_filmes.
COLUNAS_FILMES = [
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
    "provedores_atualizado_em",
    "pessoa_id",
    "data_sugestao",
    "status",
    "data_assistido",
    "nota_familia",
]


def conectar(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Abre uma conexao com o banco, criando o arquivo se nao existir.

    `row_factory` fica configurada como `sqlite3.Row` para que as linhas
    possam ser lidas tanto por indice quanto por nome de coluna.
    """
    conexao = sqlite3.connect(db_path)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON;")
    return conexao


def criar_schema(conexao: sqlite3.Connection | None = None) -> None:
    """Cria as tabelas `pessoas` e `filmes` caso ainda nao existam.

    A ordem importa: `filmes.pessoa_id` referencia `pessoas.id`.
    """
    conexao_propria = conexao is None
    conn = conexao or conectar()
    try:
        conn.execute(CRIAR_TABELA_PESSOAS)
        conn.execute(CRIAR_TABELA_FILMES)
        conn.commit()
    finally:
        if conexao_propria:
            conn.close()


def inicializar_banco(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Garante que o arquivo do banco e o schema existem e devolve a conexao."""
    conn = conectar(db_path)
    criar_schema(conn)
    return conn


def inserir_filme(conexao: sqlite3.Connection, filme: dict[str, Any]) -> int:
    """Insere um filme na tabela e devolve o `id` gerado.

    `filme` e um dicionario com qualquer subconjunto das colunas de
    `COLUNAS_FILMES`; colunas ausentes ficam com NULL.
    """
    colunas = [coluna for coluna in COLUNAS_FILMES if coluna in filme]
    valores = [filme[coluna] for coluna in colunas]
    placeholders = ", ".join("?" for _ in colunas)
    colunas_sql = ", ".join(colunas)

    cursor = conexao.execute(
        f"INSERT INTO filmes ({colunas_sql}) VALUES ({placeholders});",
        valores,
    )
    conexao.commit()
    return cursor.lastrowid


def listar_filmes(conexao: sqlite3.Connection) -> list[sqlite3.Row]:
    """Lista todos os filmes cadastrados, do mais recente para o mais antigo."""
    cursor = conexao.execute("SELECT * FROM filmes ORDER BY id DESC;")
    return cursor.fetchall()


if __name__ == "__main__":
    # Execucao manual: garante que o banco e a tabela existem.
    conexao = inicializar_banco()
    print(f"Banco pronto em: {DB_PATH}")
    conexao.close()
