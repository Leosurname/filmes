# Filmes da Família

Veja o `plan.md` para o contexto completo do projeto.

## Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Rodar

```bash
uvicorn app.main:app --reload
```

Abra http://127.0.0.1:8000 no navegador. O banco (`filmes.db`) é criado
automaticamente na primeira execução, já com alguns filmes de exemplo na
lista "Quero ver".

## O que já existe hoje

- Lista "Quero ver" e "Já assistimos", cada uma com os filmes cadastrados.
- Botão para marcar um filme como assistido (grava a data) e para desfazer,
  seja pelo aviso que aparece na hora ou pelo botão "Desfazer" no próprio
  card do filme já assistido.

O restante das fases (cadastro de filme por link, metadados da OMDb/TMDB,
filtros, identificação por nome) está descrito no `plan.md` e entra por
issues separadas.
