# Filmes da Família — Plano do Sistema

## Problema

A família manda link de filme no grupo e o link some. Ninguém lembra o que já foi
sugerido, quanto tempo o filme dura, se é apropriado para as crianças, nem em qual
serviço dá para assistir. Na hora de escolher, todo mundo fica rolando o histórico
da conversa.

## Objetivo

Uma lista única da casa. Qualquer pessoa cola o link numa página simples, o sistema
descobre sozinho os dados do filme e organiza tudo por:

- **Duração** — até 90 min, 90 a 120 min, mais de 2 h
- **Tema** — gênero (comédia, terror, animação, drama…)
- **Classificação** — livre, 10, 12, 14, 16, 18
- **Onde assistir** — Netflix, Apple TV, Prime Video, Disney+, HBO Max…

## Como funciona

1. Alguém abre a página no celular e cola o link do filme.
2. Escreve o nome (quem sugeriu) e envia.
3. O back-end identifica o filme a partir do link e busca os metadados.
4. O filme entra na lista, já com duração, gênero, classificação, nota e onde assistir.
5. Todos veem a lista e filtram pelo que importa naquela noite.

## Stack

**Front-end** — HTML, CSS e JavaScript puro. Sem framework, sem build.
Três arquivos: `index.html`, `style.css`, `app.js`.

**Back-end** — Python com FastAPI, servindo uma API JSON e os arquivos estáticos.

**Banco** — SQLite em arquivo (`filmes.db`). Não precisa de servidor de banco.

## Fonte dos dados — atenção

O IMDb **não** tem API pública gratuita. O caminho prático é:

- **OMDb API** (`omdbapi.com`) — serve os dados do IMDb: título, ano, duração,
  gêneros, classificação (`Rated`) e nota IMDb. A chave é gratuita.
- **TMDB `/watch/providers`** — só para "onde assistir" no Brasil. A OMDb não
  informa streaming, então essa parte precisa de uma segunda chave (também gratuita).

**Plano B**, se não quiser duas chaves: ler a própria página do IMDb e extrair os
dados do HTML. Funciona, mas quebra quando o IMDb muda o layout. A recomendação é
usar as duas APIs.

## Modelo de dados

Tabela `filmes`:

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER | chave primária |
| `url_original` | TEXT | o link que a pessoa colou |
| `imdb_id` | TEXT | ex.: `tt0111161` |
| `titulo` | TEXT | título do filme |
| `ano` | INTEGER | ano de lançamento |
| `duracao_min` | INTEGER | duração em minutos |
| `generos` | TEXT | lista separada por vírgula |
| `classificacao` | TEXT | classificação indicativa |
| `nota_imdb` | REAL | nota de 0 a 10 |
| `sinopse` | TEXT | resumo curto |
| `poster_url` | TEXT | imagem do pôster |
| `provedores` | TEXT (JSON) | onde assistir |
| `quem_sugeriu` | TEXT | nome de quem mandou |
| `data_sugestao` | TEXT | data de entrada |
| `status` | TEXT | `quero_ver` ou `assistido` |
| `nota_familia` | REAL | nota que a família deu depois |

## Organização e filtros

**Filtros combináveis:** faixa de duração, gênero, classificação e provedor.

**Ordenações:** mais recente, maior nota IMDb, menor duração.

**Visões:** "quero ver" (padrão) e "já assistimos".

## Estrutura de pastas

```
filmes/
  app/
    main.py        # rotas da API e servidor
    db.py          # criação do banco e queries
    metadata.py    # busca na OMDb e na TMDB
  static/
    index.html
    style.css
    app.js
  filmes.db
  .env.example     # OMDB_API_KEY, TMDB_API_KEY
  requirements.txt
  plan.md
  claude.md
  README.md
```

## Fases de entrega

| Fase | O que entrega |
|---|---|
| F1 | Página com campo de link, salvar no banco e listar |
| F2 | Enriquecer o filme com os dados da OMDb |
| F3 | Filtros e agrupamentos por duração, tema e classificação |
| F4 | "Onde assistir" via TMDB |
| F5 | Marcar como assistido e dar nota da família |
| F6 | Rodar em casa para todos acessarem pela rede |

Cada fase vira uma issue no GitHub, conforme as regras do `claude.md`.

## Fora de escopo por enquanto

- Login por pessoa (a lista é da casa toda, sem senha)
- Aplicativo mobile nativo
- Notificações
- Recomendações automáticas
