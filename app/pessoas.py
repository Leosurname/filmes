"""Quem é quem na casa, sem senha.

A lista é da casa e roda na rede de casa, então não existe autenticação. A
identificação serve só para saber quem colocou cada filme na lista.

O cuidado central é não duplicar pessoa: "João", "joao" e " JOÃO " são a mesma
pessoa. Para isso cada nome é guardado junto com uma forma normalizada — sem
acento, minúscula, sem espaço sobrando — e é por ela que a busca acontece.
"""

import unicodedata
from datetime import date


def normalizar(nome: str) -> str:
    """Reduz o nome à forma usada para comparação.

    Tira acentos, espaços das pontas, colapsa espaços internos e passa para
    minúsculas. É isso que impede "João" e "joao" de virarem duas pessoas.
    """
    if not nome:
        return ""
    sem_acento = "".join(
        letra
        for letra in unicodedata.normalize("NFD", nome)
        if unicodedata.category(letra) != "Mn"
    )
    return " ".join(sem_acento.split()).lower()


def resolver(conexao, nome: str) -> int:
    """Devolve o id da pessoa com esse nome, criando o registro na primeira vez.

    Nome novo cria a pessoa; nome que já existe reaproveita a mesma, mesmo
    digitado com acento ou caixa diferente, e mesmo vindo de outro aparelho.
    """
    limpo = " ".join((nome or "").split())
    if not limpo:
        raise ValueError("Nome vazio.")

    chave = normalizar(limpo)
    linha = conexao.execute(
        "SELECT id FROM pessoas WHERE nome_normalizado = ?", (chave,)
    ).fetchone()
    if linha is not None:
        return linha["id"]

    cursor = conexao.execute(
        "INSERT INTO pessoas (nome, nome_normalizado, data_entrada) VALUES (?, ?, ?)",
        (limpo, chave, date.today().isoformat()),
    )
    conexao.commit()
    return cursor.lastrowid


def buscar_por_id(conexao, pessoa_id: int):
    """Devolve a pessoa, ou None se o id não existir mais."""
    return conexao.execute(
        "SELECT id, nome, data_entrada FROM pessoas WHERE id = ?", (pessoa_id,)
    ).fetchone()
