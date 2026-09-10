"""Testes de app/metadata.py — integração com a OMDb.

Roda com: python -m unittest tests/test_metadata.py
"""
import json
import unittest
from unittest.mock import patch, MagicMock

from app import metadata


RESPOSTA_SHAWSHANK = {
    "Title": "The Shawshank Redemption",
    "Year": "1994",
    "Rated": "R",
    "Runtime": "142 min",
    "Genre": "Drama",
    "Plot": "Two imprisoned men bond over a number of years.",
    "imdbRating": "9.3",
    "Response": "True",
}

RESPOSTA_SERIE = {
    "Title": "Breaking Bad",
    "Year": "2008–2013",
    "Rated": "TV-MA",
    "Runtime": "49 min",
    "Genre": "Crime, Drama, Thriller",
    "Plot": "A chemistry teacher diagnosed with cancer.",
    "imdbRating": "9.5",
    "Response": "True",
}

RESPOSTA_NAO_ENCONTRADO = {"Response": "False", "Error": "Incorrect IMDb ID."}


def _mock_get(json_payload, status_ok=True):
    resposta = MagicMock()
    resposta.json.return_value = json_payload
    resposta.raise_for_status = MagicMock()
    if not status_ok:
        resposta.raise_for_status.side_effect = metadata.requests.HTTPError("erro")
    return resposta


class TestBuscarMetadados(unittest.TestCase):
    def setUp(self):
        patcher_key = patch.object(metadata, "_get_api_key", return_value="chave-fake")
        self.addCleanup(patcher_key.stop)
        patcher_key.start()

    @patch.object(metadata.requests, "get")
    def test_filme_encontrado_mapeia_todos_os_campos(self, mock_get):
        mock_get.return_value = _mock_get(RESPOSTA_SHAWSHANK)

        resultado = metadata.buscar_metadados("tt0111161")

        self.assertEqual(
            resultado,
            {
                "titulo": "The Shawshank Redemption",
                "ano": 1994,
                "duracao_min": 142,
                "generos": "Drama",
                # Desde o #51 a classificacao vem convertida para o padrao brasileiro.
                "classificacao": "16",
                "nota_imdb": 9.3,
                "sinopse": "Two imprisoned men bond over a number of years.",
            },
        )
        self.assertIsInstance(resultado["duracao_min"], int)
        self.assertIsInstance(resultado["ano"], int)
        chamada = mock_get.call_args
        self.assertEqual(chamada.kwargs["params"]["i"], "tt0111161")
        self.assertEqual(chamada.kwargs["params"]["apikey"], "chave-fake")

    @patch.object(metadata.requests, "get")
    def test_generos_multiplos_ficam_pesquisaveis(self, mock_get):
        mock_get.return_value = _mock_get(RESPOSTA_SERIE)

        resultado = metadata.buscar_metadados("tt0903747")

        self.assertEqual(resultado["generos"], "Crime, Drama, Thriller")
        self.assertIn("Drama", resultado["generos"].split(", "))
        self.assertEqual(resultado["ano"], 2008)  # pega o ano de inicio, nao o range

    @patch.object(metadata.requests, "get")
    def test_filme_nao_encontrado_retorna_none(self, mock_get):
        mock_get.return_value = _mock_get(RESPOSTA_NAO_ENCONTRADO)

        resultado = metadata.buscar_metadados("tt0000000")

        self.assertIsNone(resultado)

    @patch.object(metadata.requests, "get")
    def test_erro_de_rede_retorna_none_em_vez_de_lancar(self, mock_get):
        mock_get.side_effect = metadata.requests.ConnectionError("sem rede")

        resultado = metadata.buscar_metadados("tt0111161")

        self.assertIsNone(resultado)

    @patch.object(metadata.requests, "get")
    def test_resposta_http_de_erro_retorna_none(self, mock_get):
        mock_get.return_value = _mock_get({}, status_ok=False)

        resultado = metadata.buscar_metadados("tt0111161")

        self.assertIsNone(resultado)

    @patch.object(metadata.requests, "get")
    def test_json_invalido_retorna_none(self, mock_get):
        resposta = MagicMock()
        resposta.raise_for_status = MagicMock()
        resposta.json.side_effect = json.JSONDecodeError("erro", "doc", 0)
        mock_get.return_value = resposta

        resultado = metadata.buscar_metadados("tt0111161")

        self.assertIsNone(resultado)

    def test_sem_chave_de_api_retorna_none_sem_chamar_rede(self):
        with patch.object(metadata, "_get_api_key", return_value=None):
            with patch.object(metadata.requests, "get") as mock_get:
                resultado = metadata.buscar_metadados("tt0111161")
                mock_get.assert_not_called()
        self.assertIsNone(resultado)

    def test_sem_imdb_id_retorna_none(self):
        self.assertIsNone(metadata.buscar_metadados(""))


class TestParsers(unittest.TestCase):
    def test_parse_duracao_extrai_numero(self):
        self.assertEqual(metadata._parse_duracao_min("142 min"), 142)
        self.assertIsInstance(metadata._parse_duracao_min("142 min"), int)

    def test_parse_duracao_ausente(self):
        self.assertIsNone(metadata._parse_duracao_min("N/A"))
        self.assertIsNone(metadata._parse_duracao_min(None))

    def test_parse_ano_com_faixa(self):
        self.assertEqual(metadata._parse_ano("2008–2013"), 2008)

    def test_parse_nota_ausente(self):
        self.assertIsNone(metadata._parse_nota("N/A"))

    def test_parse_generos_normaliza_espacos(self):
        self.assertEqual(metadata._parse_generos("Drama,  Crime ,Thriller"), "Drama, Crime, Thriller")


if __name__ == "__main__":
    unittest.main()
