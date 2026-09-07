# Regras de trabalho — Claude neste repositório

Estas regras valem para **toda** tarefa feita aqui. Não são sugestões.

## 1. Issue para tudo

Nenhuma mudança começa sem uma issue no GitHub. Antes de escrever qualquer código,
crie a issue:

```bash
gh issue create --title "Filtro por duração na lista" \
  --body "O que é: ...\n\nCritério de aceite: ..." \
  --label feature,frontend
```

Toda issue precisa de:

- **Título curto** — o que vai ser feito, em uma linha
- **Descrição** — o que é e por que precisa existir
- **Critério de aceite** — como saber que ficou pronto
- **Labels** — tipo e área

Se a tarefa for grande, quebre em várias issues menores em vez de abrir uma só gigante.

## 2. Labels padrão

**Tipo:** `feature`, `bug`, `docs`, `infra`
**Área:** `frontend`, `backend`
**Prioridade:** `p0` (urgente), `p1` (importante), `p2` (quando der)

Toda issue leva pelo menos um tipo e uma área.

## 3. Uma branch por issue

Nunca commite direto na `main`. O nome da branch carrega o número da issue:

```
feat/12-filtro-duracao
fix/13-link-invalido
docs/14-atualizar-readme
```

## 4. Commits

Mensagem no imperativo, curta e direta. Referencie a issue:

```
Adicionar filtro por faixa de duração

Closes #12
```

## 5. PR sempre

Todo trabalho entra por pull request. Nunca faça merge direto.

```bash
gh pr create --title "Filtro por duração" --body "..."
```

O corpo do PR precisa ter:

- **O que mudou** — resumo em poucas linhas
- **Como testar** — os passos exatos para conferir
- **`Closes #12`** — para a issue fechar sozinha quando o PR entrar

## 6. Entregar o link do PR

**Obrigatório.** Ao terminar qualquer tarefa, a resposta para o Leo tem que incluir:

- a URL da issue
- a URL do PR

Nunca termine uma tarefa dizendo apenas "pronto". O link do PR é a entrega.

## 7. Manter tudo atualizado e organizado

- Se uma decisão do `plan.md` mudar durante o trabalho, atualize o `plan.md` **no
  mesmo PR**. O plano nunca pode ficar desatualizado em relação ao código.
- Mantenha o `README.md` com o passo a passo de instalar e rodar o projeto.
- Não deixe issue órfã: se algo foi feito, a issue correspondente fecha.
- Não deixe branch morta: depois do merge, apague a branch.
- Quando concluir uma fase do `plan.md`, marque a fase como entregue.

## 8. Segredos

Chaves de API (`OMDB_API_KEY`, `TMDB_API_KEY`) ficam no `.env`, que **nunca** vai para
o Git. O repositório guarda só o `.env.example` com os nomes das variáveis, sem valores.

## 9. Como rodar e testar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # opcional: preencher OMDB_API_KEY para buscar metadados de verdade
uvicorn app.main:app --reload
```

Depois abra `http://localhost:8000`. Sem `OMDB_API_KEY` configurada (ou com a API fora
do ar, ou com um link sem id de filme reconhecível), o filme ainda é salvo, aparece um
aviso no card e dá para preencher os dados manualmente ali mesmo.
