# V-Maps API - FastAPI Backend

## Visão Geral

Esta é a API backend do V-Maps construída com FastAPI, substituindo a integração anterior com Supabase. A API oferece funcionalidades para compartilhamento de mapas e lugares entre amigos.

## Stack Tecnológica

- **FastAPI** - Framework web assíncrono
- **SQLAlchemy 2.0** - ORM com suporte async
- **PostgreSQL** - Banco de dados via asyncpg
- **Alembic** - Migrações de banco de dados
- **Pydantic** - Validação de dados
- **JWT** - Autenticação com python-jose
- **Passlib** - Hash de senhas com bcrypt

## Estrutura do Projeto

```
api/
├── alembic/                 # Migrações do banco
│   ├── versions/            # Scripts de migração
│   ├── env.py               # Configuração do Alembic
│   └── script.py.mako       # Template de migração
├── app/
│   ├── models/              # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py          # Profile (usuário)
│   │   ├── map.py           # Map, MapMember, MapInvite
│   │   ├── place.py         # Place
│   │   ├── check_in.py      # CheckIn
│   │   └── chat.py          # ChatMessage
│   ├── schemas/             # Schemas Pydantic
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── map.py
│   │   ├── place.py
│   │   ├── check_in.py
│   │   └── chat.py
│   ├── routers/             # Endpoints da API
│   │   ├── __init__.py
│   │   ├── auth.py          # Autenticação
│   │   ├── users.py         # Gerenciamento de usuários
│   │   ├── maps.py          # CRUD de mapas
│   │   ├── places.py        # CRUD de lugares
│   │   ├── check_ins.py     # Check-ins
│   │   └── chat.py          # Mensagens de chat
│   ├── utils/               # Utilitários
│   │   ├── __init__.py
│   │   ├── auth.py          # JWT e autenticação
│   │   └── dependencies.py  # Dependências FastAPI
│   ├── config.py            # Configurações
│   ├── database.py          # Conexão com banco
│   └── main.py              # Aplicação principal
├── alembic.ini              # Configuração Alembic
├── requirements.txt         # Dependências Python
├── run.py                   # Script de desenvolvimento
└── .env.example             # Variáveis de ambiente
```

## Instalação

### 1. Criar ambiente virtual

```bash
cd api
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas configurações
# DATABASE_URL, JWT_SECRET, etc.
```

### 4. Criar banco de dados

```bash
# PostgreSQL deve estar rodando
createdb vmaps_db

# Rodar migrações
alembic upgrade head
```

### 5. Iniciar servidor

```bash
# Desenvolvimento
python run.py

# Ou diretamente com uvicorn
uvicorn app.main:app --reload --port 8000
```

## Endpoints da API

### Autenticação (`/auth`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/auth/signup` | Registro de novo usuário |
| POST | `/auth/login` | Login (retorna tokens) |
| POST | `/auth/refresh` | Renovar access token |
| POST | `/auth/logout` | Logout (invalidar token) |

#### Signup
```json
POST /auth/signup
{
  "email": "user@example.com",
  "password": "senha123",
  "display_name": "Nome do Usuário"
}
```

#### Login
```json
POST /auth/login
{
  "email": "user@example.com",
  "password": "senha123"
}

// Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "Nome"
  }
}
```

### Usuários (`/users`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/users/me` | Obter perfil do usuário atual |
| PUT | `/users/me` | Atualizar perfil |
| GET | `/users/{user_id}` | Obter perfil de outro usuário |

### Mapas (`/maps`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/maps` | Listar mapas do usuário |
| POST | `/maps` | Criar novo mapa |
| GET | `/maps/{map_id}` | Detalhes do mapa |
| PUT | `/maps/{map_id}` | Atualizar mapa |
| DELETE | `/maps/{map_id}` | Deletar mapa |
| GET | `/maps/{map_id}/members` | Listar membros |
| POST | `/maps/{map_id}/invite` | Convidar membro |
| POST | `/maps/invites/{invite_id}/accept` | Aceitar convite |
| DELETE | `/maps/{map_id}/members/{user_id}` | Remover membro |

### Lugares (`/places`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/places?map_id={id}` | Listar lugares do mapa |
| POST | `/places` | Adicionar lugar |
| GET | `/places/{place_id}` | Detalhes do lugar |
| PUT | `/places/{place_id}` | Atualizar lugar |
| DELETE | `/places/{place_id}` | Remover lugar |

### Check-ins (`/check-ins`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/check-ins?map_id={id}` | Listar check-ins do mapa |
| POST | `/check-ins` | Fazer check-in |
| GET | `/check-ins/{id}` | Detalhes do check-in |
| DELETE | `/check-ins/{id}` | Deletar check-in |

### Chat (`/chat`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/chat/{map_id}/messages` | Listar mensagens |
| POST | `/chat/{map_id}/messages` | Enviar mensagem |
| PUT | `/chat/messages/{id}` | Editar mensagem |
| DELETE | `/chat/messages/{id}` | Deletar mensagem |

## Autenticação

A API usa JWT (JSON Web Tokens) para autenticação:

1. **Access Token**: Token de curta duração (30 min) usado para autenticar requests
2. **Refresh Token**: Token de longa duração (7 dias) usado para obter novos access tokens

### Headers

```
Authorization: Bearer <access_token>
```

### Fluxo de Autenticação

```
1. POST /auth/login → access_token + refresh_token
2. Use access_token em todas as requests
3. Quando access_token expira, POST /auth/refresh com refresh_token
4. Obter novo access_token
```

## Modelos de Dados

### Profile (Usuário)
```python
{
    "id": "uuid",
    "email": "string",
    "display_name": "string",
    "avatar_url": "string | null",
    "bio": "string | null",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Map
```python
{
    "id": "uuid",
    "name": "string",
    "description": "string | null",
    "cover_url": "string | null",
    "is_public": "boolean",
    "owner_id": "uuid",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Place
```python
{
    "id": "uuid",
    "map_id": "uuid",
    "name": "string",
    "description": "string | null",
    "address": "string | null",
    "latitude": "float",
    "longitude": "float",
    "category": "string | null",
    "google_place_id": "string | null",
    "image_url": "string | null",
    "added_by": "uuid",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### CheckIn
```python
{
    "id": "uuid",
    "place_id": "uuid",
    "user_id": "uuid",
    "comment": "string | null",
    "rating": "integer (1-5) | null",
    "photo_url": "string | null",
    "created_at": "datetime"
}
```

### ChatMessage
```python
{
    "id": "uuid",
    "map_id": "uuid",
    "user_id": "uuid",
    "content": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

## Variáveis de Ambiente

```env
# Banco de Dados
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/vmaps_db

# JWT
JWT_SECRET=sua-chave-secreta-super-segura
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Frontend
FRONTEND_URL=http://localhost:5173

# Uploads
UPLOAD_DIR=./uploads
```

## Migrações

### Criar nova migração

```bash
alembic revision --autogenerate -m "descrição da mudança"
```

### Aplicar migrações

```bash
alembic upgrade head
```

### Reverter migração

```bash
alembic downgrade -1
```

### Ver histórico

```bash
alembic history
```

## Desenvolvimento

### Rodar em modo desenvolvimento

```bash
python run.py
```

A API estará disponível em:
- **API**: http://localhost:8000
- **Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testar endpoints

Use a documentação interativa em `/docs` ou ferramentas como curl/httpie:

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"senha123"}'

# Listar mapas (autenticado)
curl http://localhost:8000/maps \
  -H "Authorization: Bearer eyJ..."
```

## Próximos Passos

- [ ] WebSocket para chat em tempo real
- [ ] WebSocket para feed de atividades
- [ ] Upload de arquivos para S3/MinIO
- [ ] Integração com Google Places API
- [ ] Notificações push
- [ ] Rate limiting
- [ ] Testes automatizados
