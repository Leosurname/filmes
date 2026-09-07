"""Busca de onde assistir cada filme, via TMDB.

A OMDb não informa em quais serviços de streaming um filme está disponível,
por isso essa parte usa uma API separada: a TMDB (`themoviedb.org`).

A chave da API (`TMDB_API_KEY`) é lida do `.env` e nunca fica hardcoded aqui.
"""

import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Região usada para todas as buscas de "onde assistir": Brasil.
REGIAO = "BR"

# Estrutura vazia devolvida sempre que não há informação de provedores
# (filme não encontrado na TMDB, sem serviços no Brasil, erro de rede, etc.).
_PROVEDORES_VAZIO = {"assinatura": [], "aluguel": [], "compra": []}


def _tmdb_id_a_partir_do_imdb(imdb_id: str) -> Optional[int]:
    """Descobre o id interno da TMDB a partir de um `imdb_id` (ex.: ``tt0111161``).

    Devolve ``None`` se o filme não for encontrado ou se algo der errado
    (rede, chave inválida, resposta inesperada) — nunca lança exceção.
    """
    if not imdb_id or not TMDB_API_KEY:
        return None

    try:
        resposta = requests.get(
            f"{TMDB_BASE_URL}/find/{imdb_id}",
            params={"api_key": TMDB_API_KEY, "external_source": "imdb_id"},
            timeout=10,
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except (requests.RequestException, ValueError):
        return None

    resultados = dados.get("movie_results") or []
    if not resultados:
        return None

    return resultados[0].get("id")


def buscar_provedores(imdb_id: str) -> dict:
    """Busca onde assistir um filme no Brasil, via TMDB.

    Devolve um dicionário no formato gravado no campo `provedores`::

        {
            "assinatura": ["Netflix", "Amazon Prime Video"],
            "aluguel": ["Apple TV"],
            "compra": ["Apple TV"],
        }

    Um filme que não está disponível em nenhum serviço (ou que não foi
    encontrado na TMDB, ou que deu erro na chamada) devolve a estrutura
    vazia acima — a função nunca lança exceção.
    """
    tmdb_id = _tmdb_id_a_partir_do_imdb(imdb_id)
    if tmdb_id is None:
        return dict(_PROVEDORES_VAZIO)

    try:
        resposta = requests.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}/watch/providers",
            params={"api_key": TMDB_API_KEY},
            timeout=10,
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except (requests.RequestException, ValueError):
        return dict(_PROVEDORES_VAZIO)

    resultado_br = (dados.get("results") or {}).get(REGIAO) or {}

    def _nomes(chave: str) -> list:
        return [item["provider_name"] for item in resultado_br.get(chave, [])]

    return {
        "assinatura": _nomes("flatrate"),
        "aluguel": _nomes("rent"),
        "compra": _nomes("buy"),
    }
