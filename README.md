# Filmes da Família

Lista de filmes da casa, separada em duas visões: **quero ver** (padrão) e
**já assistimos**.

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

Acesse http://localhost:8000

Na primeira execução o banco `filmes.db` é criado e populado com alguns
filmes de exemplo (parte já marcada como "assistido", com data e nota da
família).
