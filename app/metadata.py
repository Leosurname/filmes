"""Extração do id do filme a partir do link e busca de metadados na OMDb.

Escopo desta issue (#9): a extração/busca aqui é a versão mínima necessária
para exercitar o tratamento de link inválido, filme não encontrado e API
fora do ar. A extração completa de outros serviços e a integração final com
OMDb/TMDB (issues #7, #8, #15) podem evoluir esta função sem mudar o
contrato usado pela issue #9: `buscar_metadados` nunca levanta exceção, ela
sempre devolve um resultado com um aviso quando algo dá errado.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional

import httpx

OMDB_URL = "https://www.omdbapi.com/"

_IMDB_ID_RE = re.compile(r"(tt\d{7,8})")


@dataclass
class ResultadoMetadados:
    imdb_id: Optional[str] = None
    titulo: Optional[str] = None
    ano: Optional[int] = None
    duracao_min: Optional[int] = None
    generos: Optional[str] = None
    classificacao: Optional[str] = None
    nota_imdb: Optional[float] = None
    sinopse: Optional[str] = None
    poster_url: Optional[str] = None
    incompleto: bool = False
    aviso: Optional[str] = None


def extrair_imdb_id(url: str) -> Optional[str]:
    """Tenta achar um id do tipo ttXXXXXXX em qualquer lugar da URL."""
    if not url:
        return None
    match = _IMDB_ID_RE.search(url)
    return match.group(1) if match else None


def _parse_runtime(valor: Optional[str]) -> Optional[int]:
    if not valor:
        return None
    match = re.search(r"(\d+)", valor)
    return int(match.group(1)) if match else None


def _parse_rating(valor: Optional[str]) -> Optional[float]:
    try:
        return float(valor) if valor and valor != "N/A" else None
    except (TypeError, ValueError):
        return None


def _parse_year(valor: Optional[str]) -> Optional[int]:
    if not valor:
        return None
    match = re.search(r"(\d{4})", valor)
    return int(match.group(1)) if match else None


def buscar_metadados(url: str) -> ResultadoMetadados:
    """Nunca lança exceção. Sempre devolve um ResultadoMetadados.

    Cenários tratados:
    - link em que não dá para identificar nenhum id de filme
    - filme não encontrado na OMDb
    - OMDb fora do ar / timeout / erro de rede
    - chave da OMDb não configurada (ambiente de desenvolvimento)
    """
    imdb_id = extrair_imdb_id(url)

    if not imdb_id:
        return ResultadoMetadados(
            incompleto=True,
            aviso=(
                "Não foi possível identificar o filme a partir desse link. "
                "O link foi salvo; complete os dados manualmente."
            ),
        )

    api_key = os.getenv("OMDB_API_KEY")
    if not api_key:
        return ResultadoMetadados(
            imdb_id=imdb_id,
            incompleto=True,
            aviso=(
                "Busca automática de dados não está configurada. "
                "O filme foi salvo; complete os dados manualmente."
            ),
        )

    try:
        resposta = httpx.get(
            OMDB_URL,
            params={"i": imdb_id, "apikey": api_key},
            timeout=5.0,
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except (httpx.HTTPError, ValueError):
        return ResultadoMetadados(
            imdb_id=imdb_id,
            incompleto=True,
            aviso=(
                "Não foi possível buscar os dados do filme agora "
                "(serviço externo indisponível). O filme foi salvo; "
                "tente completar os dados manualmente ou mais tarde."
            ),
        )

    if dados.get("Response") == "False":
        return ResultadoMetadados(
            imdb_id=imdb_id,
            incompleto=True,
            aviso=(
                f"Filme não encontrado ({dados.get('Error', 'sem detalhes')}). "
                "O filme foi salvo; complete os dados manualmente."
            ),
        )

    return ResultadoMetadados(
        imdb_id=imdb_id,
        titulo=dados.get("Title"),
        ano=_parse_year(dados.get("Year")),
        duracao_min=_parse_runtime(dados.get("Runtime")),
        generos=dados.get("Genre"),
        classificacao=dados.get("Rated"),
        nota_imdb=_parse_rating(dados.get("imdbRating")),
        sinopse=dados.get("Plot"),
        poster_url=dados.get("Poster") if dados.get("Poster") != "N/A" else None,
        incompleto=False,
        aviso=None,
    )
