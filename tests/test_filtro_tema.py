import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.db as db


def setup_module(module):
    # usa um banco temporario isolado para os testes
    db.DB_PATH = Path(__file__).resolve().parent / "test_filmes.db"
    if db.DB_PATH.exists():
        db.DB_PATH.unlink()
    db.init_db()


def teardown_module(module):
    if db.DB_PATH.exists():
        db.DB_PATH.unlink()


def test_lista_generos_so_traz_os_que_existem():
    db.inserir_filme("Toy Story", ["Animacao", "Comedia"])
    db.inserir_filme("O Exorcista", ["Terror"])

    generos = db.listar_generos()

    assert generos == ["Animacao", "Comedia", "Terror"]
    assert "Drama" not in generos


def test_filme_com_varios_generos_aparece_em_todos():
    resultado_animacao = db.listar_filmes(generos=["Animacao"])
    resultado_comedia = db.listar_filmes(generos=["Comedia"])

    assert any(f["titulo"] == "Toy Story" for f in resultado_animacao)
    assert any(f["titulo"] == "Toy Story" for f in resultado_comedia)


def test_filtro_por_tema_nao_pega_outro_genero():
    resultado = db.listar_filmes(generos=["Terror"])
    titulos = [f["titulo"] for f in resultado]

    assert titulos == ["O Exorcista"]


def test_filtro_por_tema_combina_com_outros_filtros():
    db.inserir_filme("Divertida Mente", ["Animacao", "Comedia"], duracao_min=95)
    db.inserir_filme("Frozen", ["Animacao"], duracao_min=140)

    resultado = db.listar_filmes(generos=["Animacao"], duracao_min=90, duracao_max=100)
    titulos = [f["titulo"] for f in resultado]

    assert titulos == ["Divertida Mente"]


def test_filtro_tema_multiplo_e_ou_entre_temas_selecionados():
    resultado = db.listar_filmes(generos=["Terror", "Comedia"])
    titulos = {f["titulo"] for f in resultado}

    assert "O Exorcista" in titulos
    assert "Toy Story" in titulos
    assert "Frozen" not in titulos
