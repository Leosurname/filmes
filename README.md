# Filmes da Família

Lista única de filmes para a casa: cola o link, o sistema busca os dados sozinho
(duração, gênero, classificação, nota e onde assistir) e organiza tudo para a
família escolher o que assistir. Veja o funcionamento completo em [`plan.md`](plan.md).

> Este README descreve como instalar e rodar o projeto conforme a estrutura
> definida no `plan.md`. Os arquivos de código (`app/`, `static/`) são criados
> nas fases de implementação (F1 em diante).

## Pré-requisitos

- Python 3.11 ou superior
- `pip` para instalar as dependências

## 1. Instalar as dependências

Clone o repositório, entre na pasta e crie um ambiente virtual:

```bash
git clone https://github.com/Leosurname/filmes.git
cd filmes
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configurar as chaves de API

O projeto usa duas APIs gratuitas para buscar os dados dos filmes:

- **OMDb API** — título, ano, duração, gêneros, classificação e nota IMDb.
- **TMDB API** — "onde assistir" (streaming) no Brasil.

### Como pegar a chave da OMDb

1. Acesse https://www.omdbapi.com/apikey.aspx
2. Escolha o plano **FREE** (1.000 requisições por dia) e preencha o formulário.
3. A chave chega por e-mail. Confirme o cadastro clicando no link recebido.

### Como pegar a chave da TMDB

1. Crie uma conta em https://www.themoviedb.org/signup
2. Vá em **Configurações da conta → API** (https://www.themoviedb.org/settings/api).
3. Solicite uma chave do tipo **Developer**, preenchendo o formulário com os dados
   pedidos (pode usar "uso pessoal" como finalidade).
4. A chave (API Key v3) aparece direto na página depois de aprovada.

### Onde colocar as chaves

Copie o arquivo de exemplo e preencha com as suas chaves:

```bash
cp .env.example .env
```

Edite o `.env` e preencha:

```
OMDB_API_KEY=coloque_sua_chave_aqui
TMDB_API_KEY=coloque_sua_chave_aqui
```

O `.env` nunca deve ser commitado — ele já está no `.gitignore`. Só o
`.env.example` (sem valores reais) fica versionado no repositório.

## 3. Subir o servidor

Com o ambiente virtual ativado e o `.env` configurado:

```bash
uvicorn app.main:app --reload
```

O banco SQLite (`filmes.db`) é criado automaticamente na primeira execução.

## 4. Acessar a página

Abra no navegador:

```
http://localhost:8000
```

Na primeira visita, digite seu nome — o aparelho lembra e não pergunta de novo
nas próximas vezes. Depois é só colar o link do filme e enviar.

Para acessar de outro aparelho na mesma rede de casa, use o IP da máquina que
está rodando o servidor, por exemplo `http://192.168.0.10:8000` (rode
`uvicorn app.main:app --reload --host 0.0.0.0` para aceitar conexões de fora
do `localhost`).

## Estrutura do projeto

Veja a estrutura completa de pastas e o modelo de dados em [`plan.md`](plan.md).
