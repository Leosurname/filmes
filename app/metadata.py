"""Identificacao do filme a partir do link e busca de metadados.

Duas responsabilidades, nesta ordem:

1. `extract_imdb_id` tira o `imdb_id` da URL colada, sem chamada de rede.
2. `buscar_metadados` consulta a OMDb com esse id. A OMDb serve os dados do
   IMDb, que nao tem API publica gratuita (ver "Fonte dos dados" no plan.md).

A chave e lida de OMDB_API_KEY no .env e nunca fica escrita no codigo. Quando
a chave nao esta configurada, o filme nao e encontrado, ou a chamada falha,
`buscar_metadados` devolve `None` e quem chamar deve salvar o filme mesmo
assim, so sem os metadados.
"""
from __future__ import annotations

import os
import re
from typing import Optional, TypedDict

import requests
from dotenv import load_dotenv

load_dotenv()

OMDB_URL = "https://www.omdbapi.com/"


# Casa com "tt" + um ou mais dígitos, em qualquer trecho da URL
# (path, querystring, etc.), sem exigir barras específicas ao redor.
_IMDB_ID_PATTERN = re.compile(r"(tt\d+)")


def extract_imdb_id(url: str) -> str:
    """Extrai o `imdb_id` (ex.: ``tt0111161``) de um link do IMDb.

    Funciona com qualquer formato de link do IMDb (com ou sem ``www``,
    domínio ``imdb.com`` ou ``m.imdb.com``, com ou sem barra final) e
    ignora parâmetros extras na URL (ex.: ``?ref_=...``).

    Se não for possível identificar o filme a partir da URL, devolve uma
    string vazia — nunca lança exceção.
    """
    if not url or not isinstance(url, str):
        return ""

    match = _IMDB_ID_PATTERN.search(url)
    if not match:
        return ""

    return match.group(1)

class MetadadosFilme(TypedDict):
    titulo: str
    ano: Optional[int]
    duracao_min: Optional[int]
    generos: str
    classificacao: str
    nota_imdb: Optional[float]
    sinopse: str


def _get_api_key() -> Optional[str]:
    """Le a chave da OMDb do ambiente (.env). Nunca deve vir hardcoded."""
    return os.getenv("OMDB_API_KEY")


def _valor_ausente(valor: Optional[str]) -> bool:
    return not valor or valor == "N/A"


def _parse_ano(valor: Optional[str]) -> Optional[int]:
    """'1994' -> 1994; '1994–1999' (série) -> 1994; ausente -> None."""
    if _valor_ausente(valor):
        return None
    digitos = "".join(ch for ch in valor[:4] if ch.isdigit())
    return int(digitos) if digitos else None


def _parse_duracao_min(valor: Optional[str]) -> Optional[int]:
    """'142 min' -> 142 (número, não texto); ausente -> None."""
    if _valor_ausente(valor):
        return None
    digitos = "".join(ch for ch in valor if ch.isdigit())
    return int(digitos) if digitos else None


def _parse_nota(valor: Optional[str]) -> Optional[float]:
    if _valor_ausente(valor):
        return None
    try:
        return float(valor)
    except ValueError:
        return None


def _parse_generos(valor: Optional[str]) -> str:
    """'Drama, Crime' -> 'Drama, Crime' normalizado, pronto para busca por termo."""
    if _valor_ausente(valor):
        return ""
    generos = [g.strip() for g in valor.split(",") if g.strip()]
    return ", ".join(generos)


def _parse_texto(valor: Optional[str]) -> str:
    return "" if _valor_ausente(valor) else valor


def buscar_metadados(imdb_id: str, *, timeout: float = 5.0) -> Optional[MetadadosFilme]:
    """Busca titulo, ano, duracao, generos, classificacao, nota e sinopse na OMDb.

    Recebe o imdb_id do filme (ex.: "tt0111161"). Retorna um dicionário com os
    metadados, ou `None` quando a OMDb não encontra o filme, a chave não está
    configurada, ou a chamada falha (timeout, erro de rede, resposta
    inválida). Em qualquer um desses casos o filme deve ser salvo mesmo
    assim, só sem os metadados.
    """
    api_key = _get_api_key()
    if not api_key or not imdb_id:
        return None

    try:
        resposta = requests.get(
            OMDB_URL,
            params={"i": imdb_id, "apikey": api_key, "plot": "short"},
            timeout=timeout,
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except (requests.RequestException, ValueError):
        return None

    if dados.get("Response") != "True":
        return None

    return MetadadosFilme(
        titulo=_parse_texto(dados.get("Title")),
        ano=_parse_ano(dados.get("Year")),
        duracao_min=_parse_duracao_min(dados.get("Runtime")),
        generos=_parse_generos(dados.get("Genre")),
        classificacao=_parse_texto(dados.get("Rated")),
        nota_imdb=_parse_nota(dados.get("imdbRating")),
        sinopse=_parse_texto(dados.get("Plot")),
    )
