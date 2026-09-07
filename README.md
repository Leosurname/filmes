# Filmes da Familia

Veja o contexto completo em `plan.md`.

## Como instalar e rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

A pagina fica em `http://localhost:8000`.

O banco `filmes.db` (SQLite) e criado automaticamente na primeira execucao.

## Rodando os testes

```bash
pip install pytest
pytest tests/
```

## Estado atual

Esta versao inicial cobre o filtro por tema (genero) descrito na issue #12:
cadastro simples de filme (titulo + generos) e listagem filtrada por tema,
combinando com outros filtros que a API aceite (ex.: faixa de duracao). O
fluxo completo de colar link e buscar dados na OMDb, os demais filtros do
`plan.md` e as demais fases ainda serao implementados em outras issues.
