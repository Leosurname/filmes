"""Conversao de classificacao indicativa da OMDb para o padrao brasileiro.

A OMDb devolve o campo `Rated` no padrao dos EUA (MPAA) ou, para series/TV,
no padrao TV Parental Guidelines. Esse modulo converte esses valores para as
faixas usadas no Brasil: L, 10, 12, 14, 16, 18.

Quando a OMDb nao informa classificacao (`N/A`, vazio, `Not Rated`, `Unrated`),
o filme fica marcado como "nao informada" (representado por `None`).
"""

# Ordem de "peso" de cada classificacao, da mais leve para a mais pesada.
# Usada para responder perguntas do tipo "ate 12 anos" (tudo igual ou mais leve).
ORDEM_CLASSIFICACAO = ["L", "10", "12", "14", "16", "18"]

_MAPA_OMDB_PARA_BR = {
    # MPAA (filmes)
    "G": "L",
    "TV-Y": "L",
    "TV-Y7": "L",
    "TV-G": "L",
    "PG": "10",
    "TV-PG": "10",
    "PG-13": "12",
    "TV-14": "14",
    "R": "16",
    "NC-17": "18",
    "TV-MA": "18",
}

_VALORES_SEM_CLASSIFICACAO = {"", "N/A", "NOT RATED", "UNRATED", "NR"}


def omdb_para_br(rated):
    """Converte o campo `Rated` da OMDb para a classificacao brasileira.

    Retorna um dos valores de ORDEM_CLASSIFICACAO, ou None quando a
    classificacao nao foi informada / nao e reconhecida.
    """
    if rated is None:
        return None

    valor = rated.strip().upper()

    if valor in _VALORES_SEM_CLASSIFICACAO:
        return None

    return _MAPA_OMDB_PARA_BR.get(valor.replace("TV_", "TV-"))


def rotulo_classificacao(classificacao_br):
    """Rotulo legivel para exibir na interface."""
    if classificacao_br is None:
        return "Nao informada"
    if classificacao_br == "L":
        return "Livre"
    return f"{classificacao_br} anos"


def atende_filtro_ate(classificacao_br, classificacao_maxima):
    """Verifica se uma classificacao e igual ou mais leve que a maxima pedida.

    Filmes sem classificacao (None) nunca atendem a um filtro "ate X anos",
    porque nao da para garantir que sejam apropriados.
    """
    if classificacao_maxima is None:
        return True
    if classificacao_br is None:
        return False
    try:
        indice_filme = ORDEM_CLASSIFICACAO.index(classificacao_br)
        indice_maximo = ORDEM_CLASSIFICACAO.index(classificacao_maxima)
    except ValueError:
        return False
    return indice_filme <= indice_maximo
