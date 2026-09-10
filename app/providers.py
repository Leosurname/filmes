"""Busca de provedores de streaming (TMDB), usada na reconsulta periodica.

A busca completa de "onde assistir" na entrada do filme e escopo da issue
#15/#16. Aqui existe so o suficiente para a issue #17 conseguir reconsultar
um filme que ja tem `imdb_id` e atualizar o campo `provedores`.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("app.providers")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
PAIS = "BR"


def buscar_provedores_tmdb(imdb_id: str) -> dict | None:
    """Retorna o dict de provedores (BR) do TMDB para um imdb_id, ou None
    se nao foi possivel buscar (sem chave, filme nao encontrado, erro de
    rede etc). Nunca levanta excecao - quem chama trata None como "sem
    novidade, tenta na proxima".
    """
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        logger.warning("TMDB_API_KEY nao configurada; pulando reconsulta de %s", imdb_id)
        return None

    try:
        with httpx.Client(timeout=10) as client:
            achado = client.get(
                f"{TMDB_BASE_URL}/find/{imdb_id}",
                params={"api_key": api_key, "external_source": "imdb_id"},
            )
            achado.raise_for_status()
            resultados = achado.json().get("movie_results") or []
            if not resultados:
                logger.info("Filme %s nao encontrado no TMDB", imdb_id)
                return None
            tmdb_id = resultados[0]["id"]

            resp = client.get(
                f"{TMDB_BASE_URL}/movie/{tmdb_id}/watch/providers",
                params={"api_key": api_key},
            )
            resp.raise_for_status()
            return resp.json().get("results", {}).get(PAIS, {})
    except httpx.HTTPError:
        logger.exception("Falha ao reconsultar provedores do filme %s no TMDB", imdb_id)
        return None
