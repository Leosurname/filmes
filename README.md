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

Para acessar pelo celular ou por outro aparelho da casa, veja
[Rodando na rede de casa](#rodando-na-rede-de-casa) mais abaixo.

## Rodando na rede de casa

O servidor sobe aceitando conexões de qualquer aparelho da mesma rede Wi-Fi
(celular, tablet, notebook) — não só da máquina onde ele roda.

### Subir o servidor

```bash
./scripts/iniciar-servidor.sh
```

O script sempre entra na pasta do projeto antes de rodar (não importa de onde
foi chamado), garante que o servidor escuta em `0.0.0.0` — em vez de
`127.0.0.1`, que só aceitaria conexões da própria máquina — e imprime o
endereço de acesso ao iniciar.

Por baixo, ele equivale a:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Endereço de acesso pelo celular

1. Descubra o IP da máquina que vai rodar o servidor, na rede local:
   ```bash
   ipconfig getifaddr en0   # Wi-Fi, na maioria dos Macs
   ```
2. No celular (conectado à **mesma rede Wi-Fi**), abra:
   ```
   http://SEU-IP-LOCAL:8000
   ```
   Por exemplo: `http://192.168.3.152:8000`.

O IP pode mudar se o roteador reatribuir o endereço; se isso acontecer,
rode o comando do passo 1 de novo.

**Isso não expõe o serviço na internet** — só funciona para aparelhos dentro
da rede Wi-Fi de casa. Nada de redirecionamento de porta no roteador nem
túneis públicos.

Se o macOS bloquear conexões de entrada (Firewall em
*Ajustes do Sistema → Rede → Firewall*), autorize o Python/uvicorn quando o
sistema perguntar, ou libere a porta 8000 manualmente.

### Banco de dados

O banco é o arquivo `filmes.db`, na raiz do projeto (fora do Git, veja
`.gitignore`). Por ser um arquivo comum em disco — não algo em memória nem em
pasta temporária — ele **sobrevive sozinho a reinícios do servidor**: parar e
subir o processo de novo não apaga nem reseta os dados. O único cuidado é
sempre rodar o servidor a partir da mesma pasta do projeto, o que o
`scripts/iniciar-servidor.sh` já garante.

### Ligar sozinho quando o computador liga?

**Decisão: por enquanto, não.** O servidor sobe manualmente
(`./scripts/iniciar-servidor.sh`), porque o sistema ainda está em construção
(fases F1 a F5 do `plan.md` seguem pendentes) e faz mais sentido controlar
quando ele está no ar enquanto isso.

Para quem já quiser deixá-lo sempre ligado, existe um modelo pronto de
LaunchAgent do macOS em `scripts/exemplo.com.filmes.servidor.plist`. Para
ativar:

```bash
cp scripts/exemplo.com.filmes.servidor.plist ~/Library/LaunchAgents/com.filmes.servidor.plist
# edite o arquivo copiado e troque SEU_USUARIO pelo caminho real do projeto
launchctl load ~/Library/LaunchAgents/com.filmes.servidor.plist
```

Para desligar o autostart:

```bash
launchctl unload ~/Library/LaunchAgents/com.filmes.servidor.plist
```

Essa decisão pode ser revista quando as fases F1–F5 estiverem prontas.

## Estrutura do projeto

Veja a estrutura completa de pastas e o modelo de dados em [`plan.md`](plan.md).
