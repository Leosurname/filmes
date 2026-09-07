"""Extração de identificadores de filme a partir do link colado.

Por enquanto cobre apenas o IMDb: o `imdb_id` (padrão `tt` seguido de dígitos)
é extraído diretamente da URL, sem precisar de nenhuma chamada de rede.
"""

import re

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
