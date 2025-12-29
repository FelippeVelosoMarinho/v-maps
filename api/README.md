# V-Maps API

Backend FastAPI para o aplicativo V-Maps.

## Requisitos

- Python 3.11+
- PostgreSQL (ou SQLite para desenvolvimento)

## Instalação

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## Configuração

Copie o arquivo `.env.example` para `.env` e configure as variáveis:

```bash
cp .env.example .env
```

## Executar

```bash
# Desenvolvimento
uvicorn app.main:app --reload --port 8000

# Produção
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Documentação da API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estrutura do Projeto

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entrada da aplicação
│   ├── config.py            # Configurações
│   ├── database.py          # Conexão com banco
│   ├── models/              # Modelos SQLAlchemy
│   ├── schemas/             # Schemas Pydantic
│   ├── routers/             # Rotas da API
│   ├── services/            # Lógica de negócio
│   └── utils/               # Utilitários
├── alembic/                 # Migrações
├── tests/                   # Testes
├── requirements.txt
└── .env
```
