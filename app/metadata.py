"""Extração de identificadores a partir do link colado pelo usuário.

Escopo mínimo para a issue #10 (avisar sobre duplicado): só precisamos
extrair o `imdb_id` do link. A busca completa de metadados na OMDb/TMDB
fica para as issues #7 e #8.
"""

import re

# Ex.: tt0111161, tt10872600
IMDB_ID_RE = re.compile(r"(tt\d{7,8})")


def extrair_imdb_id(url: str) -> str | None:
    """Extrai o imdb_id de uma URL do IMDb (ou de um id colado direto).

    Aceita variações como:
    - https://www.imdb.com/title/tt0111161/
    - https://imdb.com/title/tt0111161/?ref_=nv_sr_srsg_0
    - m.imdb.com/title/tt0111161
    - tt0111161 (colado direto)

    Retorna None se não conseguir identificar um imdb_id no texto.
    """
    if not url:
        return None

    match = IMDB_ID_RE.search(url.strip())
    if not match:
        return None

    return match.group(1)
