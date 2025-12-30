# V-Maps API

Backend FastAPI para o aplicativo V-Maps.

## Requisitos

- Python 3.11+
- PostgreSQL (ou SQLite para desenvolvimento)
- Docker (para deploy)

## Instalação Local

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

## Executar Localmente

```bash
# Desenvolvimento
uvicorn app.main:app --reload --port 8000

# Ou usando o script
python run.py
```

## Docker

### Build da Imagem

```bash
# Build com versão específica
docker build -t v-maps-backend:1.0.0 .

# Build como latest
docker build -t v-maps-backend:latest .
```

### Executar com Docker Compose

```bash
# Subir todos os serviços (backend + db)
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

### Variáveis de Ambiente (Docker)

Crie um arquivo `.env` na pasta `api/` com:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua-senha-segura
POSTGRES_DB=v_maps

# JWT
SECRET_KEY=sua-chave-secreta-muito-segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
FRONTEND_URL=https://seu-frontend.com

# Docker
VERSION=1.0.0
```

## 🚀 Deploy no Servidor

### Processo de Deploy

1. **Clone/Atualize o repositório no servidor:**
   ```bash
   git clone <repo-url>
   # ou
   git pull origin main
   ```

2. **Build da imagem Docker com versão:**
   ```bash
   docker build -t v-maps-backend:1.0.0 .
   ```

3. **Atualize no Portainer:**
   - Acesse `tsportainer.ciano.io`
   - Abra o container desejado
   - Em **Edit**, altere a versão da imagem para a nova (ex: `1.0.0`)
   - Clique em **Rerun jobs**

### Script de Deploy (Linux/Mac)

```bash
# Dar permissão de execução
chmod +x deploy.sh

# Executar deploy com versão
./deploy.sh 1.0.0
```

### Versionamento

Use [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (ex: 1.2.3)
- MAJOR: mudanças incompatíveis
- MINOR: novas funcionalidades compatíveis
- PATCH: correções de bugs

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
│   └── utils/               # Utilitários
├── alembic/                 # Migrações
├── uploads/                 # Arquivos enviados
├── Dockerfile               # Build da imagem
├── docker-compose.yaml      # Orquestração
├── deploy.sh                # Script de deploy
├── requirements.txt
└── .env
```

## Healthcheck

A aplicação possui healthcheck configurado no Docker:
- Endpoint: `/docs`
- Intervalo: 30s
- Timeout: 10s
