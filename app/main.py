"""API e servidor de arquivos estaticos.

Este arquivo, por enquanto, so implementa o necessario para a issue #13
(filtro por classificacao indicativa): listar filmes e filtrar por
classificacao. As demais rotas (salvar filme a partir de link, onde
assistir, etc.) sao escopo de outras issues.
"""

import os

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles

from app import db
from app.classificacao import (
    ORDEM_CLASSIFICACAO,
    atende_filtro_ate,
    omdb_para_br,
    rotulo_classificacao,
)

app = FastAPI(title="Filmes da Familia")

db.inicializar()

DIR_ESTATICO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


@app.get("/api/filmes")
def obter_filmes(classificacao_max: str | None = Query(default=None)):
    """Lista os filmes, com filtro opcional de classificacao indicativa.

    `classificacao_max`: um dos valores L, 10, 12, 14, 16, 18. Quando
    informado, retorna somente filmes com classificacao igual ou mais leve.
    Filmes sem classificacao definida na OMDb nunca entram nesse filtro,
    mas aparecem normalmente quando nenhum filtro e aplicado.
    """
    if classificacao_max is not None and classificacao_max not in ORDEM_CLASSIFICACAO:
        return {"erro": f"classificacao_max invalida. Use um de: {ORDEM_CLASSIFICACAO}"}

    conexao = db.conectar()
    try:
        filmes = db.listar_filmes(conexao)
    finally:
        conexao.close()

    resultado = []
    for filme in filmes:
        classificacao_br = omdb_para_br(filme["classificacao"])

        if classificacao_max is not None and not atende_filtro_ate(
            classificacao_br, classificacao_max
        ):
            continue

        resultado.append(
            {
                "id": filme["id"],
                "titulo": filme["titulo"],
                "ano": filme["ano"],
                "classificacao": classificacao_br,
                "classificacao_rotulo": rotulo_classificacao(classificacao_br),
            }
        )

    return resultado


@app.get("/api/classificacoes")
def obter_classificacoes():
    """Lista as opcoes de classificacao, para montar o filtro na tela."""
    return [
        {"valor": valor, "rotulo": rotulo_classificacao(valor)}
        for valor in ORDEM_CLASSIFICACAO
    ]


app.mount("/", StaticFiles(directory=DIR_ESTATICO, html=True), name="static")
