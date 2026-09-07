"""Criação do banco SQLite e queries usadas pela API.

Escopo desta issue (#18 - marcar filme como assistido): o banco só precisa
guardar o suficiente para listar filmes por status e alternar entre
`quero_ver` e `assistido`, com a data em que isso aconteceu. As demais
colunas do modelo completo (ver plan.md) ficam para as issues que cuidam de
cada fase (buscar metadados, filtros, "onde assistir" etc).
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "filmes.db"

STATUS_QUERO_VER = "quero_ver"
STATUS_ASSISTIDO = "assistido"


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
                ano INTEGER,
                duracao_min INTEGER,
                generos TEXT,
                classificacao TEXT,
                nota_imdb REAL,
                poster_url TEXT,
                status TEXT NOT NULL DEFAULT 'quero_ver',
                data_sugestao TEXT NOT NULL,
                data_assistido TEXT
            )
            """
        )
        conn.commit()
        _seed_se_vazio(conn)
    finally:
        conn.close()


def _seed_se_vazio(conn: sqlite3.Connection) -> None:
    """Dados de exemplo só para dar para testar a tela sem depender das
    issues de cadastro/importação de filme (fora do escopo desta issue)."""
    total = conn.execute("SELECT COUNT(*) AS n FROM filmes").fetchone()["n"]
    if total > 0:
        return

    agora = _agora_iso()
    exemplos = [
        ("A Origem", 2010, 148, "Ficção Científica, Ação", "12", 8.8, None),
        ("Divertida Mente", 2015, 95, "Animação, Comédia", "Livre", 8.1, None),
        ("Parasita", 2019, 132, "Drama, Suspense", "16", 8.5, None),
    ]
    conn.executemany(
        """
        INSERT INTO filmes
            (titulo, ano, duracao_min, generos, classificacao, nota_imdb,
             poster_url, status, data_sugestao)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'quero_ver', ?)
        """,
        [(*exemplo, agora) for exemplo in exemplos],
    )
    conn.commit()


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def listar_por_status(status: str) -> list[dict]:
    conn = get_connection()
    try:
        ordenar_por = "data_assistido DESC" if status == STATUS_ASSISTIDO else "data_sugestao DESC"
        linhas = conn.execute(
            f"SELECT * FROM filmes WHERE status = ? ORDER BY {ordenar_por}",
            (status,),
        ).fetchall()
        return [dict(linha) for linha in linhas]
    finally:
        conn.close()


def buscar_por_id(filme_id: int) -> dict | None:
    conn = get_connection()
    try:
        linha = conn.execute(
            "SELECT * FROM filmes WHERE id = ?", (filme_id,)
        ).fetchone()
        return dict(linha) if linha else None
    finally:
        conn.close()


def atualizar_status(filme_id: int, novo_status: str) -> dict | None:
    """Move o filme entre `quero_ver` e `assistido`.

    Ao marcar como assistido, grava a data/hora. Ao desfazer (voltar para
    `quero_ver`), limpa a data — é isso que permite desfazer o clique.
    """
    if novo_status not in (STATUS_QUERO_VER, STATUS_ASSISTIDO):
        raise ValueError(f"status inválido: {novo_status}")

    data_assistido = _agora_iso() if novo_status == STATUS_ASSISTIDO else None

    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE filmes SET status = ?, data_assistido = ? WHERE id = ?",
            (novo_status, data_assistido, filme_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
    finally:
        conn.close()

    return buscar_por_id(filme_id)
