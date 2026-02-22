# 🔍 V-Maps (LUME) — Auditoria de Código, Arquitetura e Segurança

> **Objetivo:** Identificar arquivos obsoletos, revisar a arquitetura do projeto, organizar o código, detectar vulnerabilidades de segurança e propor melhorias.

---

## 🚨 Vulnerabilidades de Segurança

### CRÍTICO — Ação Imediata Necessária

#### V1. 🔴 Google Maps API Key Hardcoded no Código-Fonte

**Arquivos afetados:**

- `client/src/components/map/MapContainer.tsx` (linhas 245, 297)
- `client/src/components/social/TripBookContent.tsx` (linha 74)

```typescript
// ❌ Key visível em 3 arquivos, commitada no Git, exposta no bundle JS
apiKey = "AIzaSyDlIqw5x7Tp77QooB1OT1nQJzvuevkT1hg";
```

**Risco:** Qualquer pessoa com acesso ao bundle (ou ao Git) pode usar essa chave. O Google pode cobrar por uso indevido ou a chave pode ser utilizada para ataques de billing.

**Proposta:**

```
1. Mover para variável de ambiente: VITE_GOOGLE_MAPS_API_KEY
2. Usar import.meta.env.VITE_GOOGLE_MAPS_API_KEY no código
3. Invalidar a chave atual no Google Cloud Console
4. Gerar nova chave com restrições:
   ├── Restrição de HTTP Referrer (domínios permitidos)
   ├── Restrição de API (apenas Maps JavaScript API)
   └── Quotas de uso
5. Adicionar chave ao .env (não commitado) e .env.example (sem valor)
```

---

#### V2. 🔴 JWT Secret Key Padrão em `config.py`

**Arquivo:** `api/app/config.py` (linha 10)

```python
# ❌ Secret key padrão — se .env não definir, QUALQUER pessoa pode forjar tokens
secret_key: str = "your-super-secret-key-change-in-production"
```

**Risco:** Se o `.env` não estiver configurado em produção, tokens JWT podem ser forjados por qualquer atacante que conheça esse default. Acesso total a todas as contas.

**Proposta:**

```
1. Remover o valor default — forçar configuração via .env
   secret_key: str  # Sem default, erro na inicialização se não definido
2. Adicionar validação no startup:
   if settings.secret_key == "your-super-secret-key-change-in-production":
       raise RuntimeError("CONFIGURE SECRET_KEY NO .ENV!")
3. Gerar key com: python -c "import secrets; print(secrets.token_urlsafe(64))"
4. Documentar no README como configurar
```

---

#### V3. 🔴 Traceback Completo Exposto em Erros 500

**Arquivo:** `api/app/main.py` (linhas 99-112)

```python
# ❌ NUNCA expor traceback em produção — revela estrutura interna, paths, libs
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "traceback": error_trace,  # ← EXPÕE TRACEBACK COMPLETO
            "path": request.url.path,
            "method": request.method
        }
    )
```

**Risco:** Atacantes podem ver paths do filesystem, versões de bibliotecas, queries SQL, e estrutura interna da aplicação.

**Proposta:**

```
1. Enviar traceback apenas em modo DEV:
   content = {"error": "Internal Server Error"}
   if settings.debug:
       content["traceback"] = error_trace
2. Em produção: logar traceback no servidor, retornar mensagem genérica
3. Adicionar setting: debug: bool = False ao Config
```

---

#### V4. 🔴 Endpoint de Debug Exposto em Produção

**Arquivo:** `api/app/main.py` (linhas 114-123)

```python
# ❌ Expõe TODOS os headers da requisição, incluindo tokens de autenticação
@app.get("/debug/cors-check")
async def cors_check(request: Request):
    return {
        "headers": dict(request.headers),  # ← TOKENS EXPOSTOS
        "client": request.client.host,
    }
```

**Risco:** Se alguém enviar uma request autenticada para esse endpoint, o token Bearer é retornado no body da response. Facilita SSRF e token leaking.

**Proposta:**

```
1. Remover completamente esse endpoint em produção
2. Se necessário para debug, proteger com:
   ├── Verificação de ambiente (if settings.debug)
   ├── Autenticação admin
   └── Não retornar headers sensíveis (Authorization, Cookie)
```

---

### ALTO — Corrigir em Breve

#### V5. 🟠 Sem Rate Limiting em Nenhum Endpoint

**Situação:** Nenhum endpoint possui rate limiting. Endpoints críticos afetados:

| Endpoint             | Risco                      |
| -------------------- | -------------------------- |
| `POST /auth/login`   | Brute-force de senhas      |
| `POST /auth/signup`  | Criação em massa de contas |
| `POST /auth/refresh` | Exaustão de tokens         |
| `POST /places`       | Spam de lugares            |
| `POST /check-ins`    | Spam de check-ins          |

**Proposta:**

```
1. Instalar slowapi: pip install slowapi
2. Configurar limiter global:
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
3. Aplicar em endpoints críticos:
   @limiter.limit("5/minute")  # Login
   @limiter.limit("3/minute")  # Signup
   @limiter.limit("30/minute") # API geral
```

---

#### V6. 🟠 Sem Validação de Força de Senha

**Arquivo:** `api/app/routers/auth.py` — `signup()`

**Situação:** A senha é aceita sem qualquer validação. Um usuário pode usar senhas como `"1"` ou `""`.

**Proposta:**

```
1. No schema UserCreate, adicionar validação:
   @field_validator('password')
   def validate_password(cls, v):
       if len(v) < 8:
           raise ValueError('Senha deve ter pelo menos 8 caracteres')
       return v
2. Considerar: pelo menos 1 número, 1 letra maiúscula
```

---

#### V7. 🟠 SQL Echo Habilitado em Produção

**Arquivo:** `api/app/database.py` (linha 16)

```python
engine = create_async_engine(
    database_url,
    echo=True,  # ❌ Logs SQL completos — performance e segurança
)
```

**Risco:** Todas as queries SQL são logadas, incluindo dados sensíveis. Também degrada performance.

**Proposta:**

```
1. Condicionar ao modo debug:
   echo=settings.debug
2. Em produção: False
```

---

#### V8. 🟠 Email do Usuário Logado em Tentativas de Login

**Arquivo:** `api/app/routers/auth.py` (linha 80)

```python
logger.info(f"Tentativa de login para o email: {credentials.email}")
```

**Risco:** Logs contêm emails de usuários, violando princípios de privacidade (LGPD).

**Proposta:**

```
1. Remover email dos logs de login
2. Logar apenas: "Login attempt from IP {request.client.host}"
3. Para debug, usar hash parcial: email[:3] + "***"
```

---

#### V9. 🟠 Access Token Expira em 30 Minutos, Sem Rotação Automática

**Arquivo:** `api/app/config.py` (linha 12)

```python
access_token_expire_minutes: int = 30
```

**Situação:** O frontend (`api.ts`) tenta refresh automaticamente após erro 401, mas não faz rotação proativa. Se o token expirar durante uma ação WebSocket, a conexão cai sem aviso.

**Proposta:**

```
1. Aumentar para 60 minutos (melhor UX no mobile)
2. Implementar refresh proativo no frontend:
   ├── Timer que renova o token 5min antes de expirar
   └── Decode jwt local para extrair "exp"
3. No WebSocket: enviar mensagem de renovação via WS
```

---

#### V10. 🟠 Catch-All Route Engole Todas as 404s

**Arquivo:** `api/app/main.py` (linhas 139-156)

```python
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_all(request, path_name):
    # ❌ Retorna 200 com corpo de "Not Found" em vez de 404 real
    return {"error": "Not Found", ...}
```

**Risco:** Ferramentas de monitoramento não detectam 404, e a rota pode interceptar chamadas legítimas que deveriam 404.

**Proposta:**

```
1. Remover catch_all completamente — FastAPI já lida com 404
2. Se necessário para debug: retornar status 404 (JSONResponse com status_code=404)
3. Or: mover para middleware de logging (apenas log, não intercepta)
```

---

### MÉDIO — Melhorias Recomendadas

#### V11. 🟡 CORS Muito Permissivo

**Arquivo:** `api/app/main.py` (linhas 69-91)

```python
allow_methods=["*"],   # ← Permite TODOS os métodos HTTP
allow_headers=["*"],   # ← Permite TODOS os headers
```

**Proposta:**

```
1. Especificar métodos: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
2. Especificar headers: ["Authorization", "Content-Type"]
3. Mover origins para settings.allowed_origins (lista no .env)
4. Remover origins duplicadas (lista idêntica aparece 2 vezes no arquivo)
```

---

#### V12. 🟡 Uploads Servidos Sem Autenticação

**Arquivo:** `api/app/main.py` (linha 95)

```python
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
```

**Risco:** Qualquer pessoa pode acessar todos os uploads (fotos de check-in, avatares) bastando adivinhar a URL.

**Proposta:**

```
1. Usar nomes de arquivo com UUID (já feito parcialmente)
2. Ou: servir uploads via endpoint autenticado em vez de StaticFiles
3. Adicionar Content-Disposition headers
```

---

## 🗑️ Arquivos Obsoletos — Para Remover

### Backend (API Root)

Scripts de migração e debug que ficaram soltos na raiz do projeto:

| Arquivo                                | Motivo para Remover                         |
| -------------------------------------- | ------------------------------------------- |
| `api/add_color_column.py`              | Script de migração one-shot, já executado   |
| `api/check_schema.py`                  | Script de verificação, não faz parte da app |
| `api/check_trips_schema.py`            | Script de verificação, não faz parte da app |
| `api/fix_chat_nullability.py`          | Fix pontual, já aplicado                    |
| `api/fix_db.py`                        | Fix pontual, já aplicado                    |
| `api/fix_shared_to_feed.py`            | Fix pontual, já aplicado                    |
| `api/migrate_chat.py`                  | Migração pontual, já aplicada               |
| `api/migrate_db.py`                    | Migração pontual, já aplicada               |
| `api/test_chat_insert.py`              | Teste manual descartável                    |
| `api/verify_db_data.py`                | Script de verificação descartável           |
| `api/verify_social.py`                 | Script de verificação descartável           |
| `api/vmaps.db` / `.db-shm` / `.db-wal` | SQLite local, não deveria estar no repo     |

**Proposta:**

```
1. Mover scripts de migração para api/scripts/migrations/ (se quiser manter histórico)
2. Ou deletar completamente
3. Adicionar vmaps.db* ao .gitignore
4. Usar Alembic para migrações formais (diretório já existe)
```

---

### Frontend — Integração Supabase

A aplicação **não usa mais Supabase** (migrou para API FastAPI própria), mas os arquivos permanecem:

| Arquivo                                      | Motivo para Remover                                   |
| -------------------------------------------- | ----------------------------------------------------- |
| `client/src/integrations/supabase/client.ts` | Cria client Supabase, não é importado em nenhum lugar |
| `client/src/integrations/supabase/types.ts`  | Types do Supabase, sem uso                            |

**Proposta:**

```
1. Deletar diretório client/src/integrations/supabase/ inteiro
2. Verificar package.json: se @supabase/supabase-js está nas deps, remover
3. Remover VITE_SUPABASE_URL e VITE_SUPABASE_PUBLISHABLE_KEY do .env
```

---

### Frontend — Mock Data em Produção

**Arquivo:** `client/src/lib/mockData.ts` (266 linhas)

Este arquivo contém dados mock (usuários, lugares, check-ins, trips) destinados a **demonstração de UI**, mas suas **interfaces e helpers estão sendo importadas em produção**:

| Importador             | O que importa                 |
| ---------------------- | ----------------------------- |
| `PlaceDetailSheet.tsx` | `MockUser`, `getCategoryIcon` |
| `Index.tsx`            | `MockUser`, `getCategoryIcon` |
| `ActiveTripHUD.tsx`    | `formatDistance`              |

**Proposta:**

```
1. Mover interfaces (MockUser, MockPlace, etc.) para um types.ts apropriado
2. Mover helpers (getCategoryIcon, formatDistance, formatTimeAgo) para utils.ts
3. Remover dados mock (mockUsers, mockPlaces, mockCheckIns, etc.)
4. Ou: renomear para lib/placeUtils.ts e manter apenas interfaces + helpers
```

---

## 🏗️ Revisão de Arquitetura

### A1. 🔴 `api.ts` — Monolito de 1361 Linhas

**Arquivo:** `client/src/lib/api.ts`

Este arquivo contém TUDO: interfaces, tipos, o ApiClient inteiro com 100+ métodos, configuração de base URL, lógica de tokens, lógica de refresh automático.

**Problemas:**

- Impossível testar métodos individualmente
- Qualquer mudança toca um arquivo gigante
- Imports circulares possíveis
- Difícil de navegar e manter

**Proposta de refatoração:**

```
client/src/lib/
├── api/
│   ├── client.ts          # ApiClient base (request, tokens, auth)
│   ├── types.ts           # Todas as interfaces/types da API
│   ├── auth.ts            # Métodos de autenticação
│   ├── maps.ts            # Métodos de mapas e places
│   ├── social.ts          # Métodos sociais (check-ins, feed)
│   ├── trips.ts           # Métodos de trips
│   ├── chat.ts            # Métodos de chat
│   ├── friends.ts         # Métodos de amizades
│   ├── notifications.ts   # Métodos de notificações
│   └── index.ts           # Re-export: export { api } from './client'
```

---

### A2. 🔴 `window.location.reload()` Usado como State Manager

**Arquivo:** `client/src/contexts/TripContext.tsx` — 5 ocorrências

```typescript
// ❌ Usado em: leaveTrip, endTrip, submitTripReport, e em handlers de WS
window.location.reload();
```

**Problemas:**

- Recarregar a página inteira para atualizar state é o equivalente a reiniciar o PC quando um app trava
- Perde state de componentes não relacionados
- No Android: recarregar a WebView é lento e causa flash branco
- Mostra falta de controle sobre o state management

**Proposta:**

```
1. Substituir por invalidação de queries (react-query):
   queryClient.invalidateQueries({ queryKey: ['maps'] });
   queryClient.invalidateQueries({ queryKey: ['trips'] });
   queryClient.invalidateQueries({ queryKey: ['feed'] });
2. Resetar state local dos contexts:
   setCurrentTrip(null);
   setChatMessages([]);
   setRealTimeLocations({});
3. Navegar para página principal se necessário:
   navigate('/');
```

---

### A3. 🟠 CORS Origins Duplicadas

**Arquivo:** `api/app/main.py`

A lista de CORS origins aparece **2 vezes** — no `lifespan` (log) e no `add_middleware`. Se uma for atualizada e a outra não, haverá inconsistência.

**Proposta:**

```
1. Definir origins uma vez em settings:
   allowed_origins: list[str] = [...]
2. Referenciar em ambos os lugares:
   allow_origins=settings.allowed_origins
3. Ou mover para .env como JSON string
```

---

### A4. 🟠 `__import__` Hack no `auth.py`

**Arquivo:** `api/app/routers/auth.py` (linha 132)

```python
# ❌ Import dinâmico para evitar circular import — code smell
current_user: User = Depends(
    __import__('app.utils.dependencies', fromlist=['get_current_user']).get_current_user
)
```

**Proposta:**

```
1. Importar normalmente no topo do arquivo:
   from app.utils.dependencies import get_current_user
2. Se houver circular import, reorganizar dependências
3. Esse endpoint (/auth/me) duplica /users/me — considerar remover
```

---

### A5. 🟡 Componentes Frontend sem Organização Clara

**Estrutura atual:** 11 diretórios com mistura de responsabilidades:

```
components/
├── avatar/      # 1 componente
├── chat/        # Chat de mapa
├── groups/      # Sidebar de grupos
├── map/         # Mapa e controles
├── markers/     # Marcadores customizados
├── modals/      # Modals variados
├── navigation/  # TopBar, BottomBar, Dock
├── profile/     # Perfil e configurações
├── sidebar/     # Sidebar e drawer
├── social/      # Feed, trips, check-ins (MISTURA DE TUDO)
├── ui/          # Shadcn components
```

**Problemas:**

- `social/` é um diretório catch-all com 20+ componentes:
  - `PlaceDetailSheet.tsx` (detalhes de lugar — deveria ser em `map/` ou `places/`)
  - `TripPanel.tsx`, `TripBottomBar.tsx`, `TripCallInterface.tsx`, `TripReportModal.tsx` (todos de Trip — deveria ser `trip/`)
  - `CheckInModal.tsx`, `ActivityFeed.tsx` (feed — ok em `social/`)
  - `TwitterFeed.tsx`, `FeedOverlay.tsx` (feed/social)
  - `IncomingCallModal.tsx` (trip — deveria ser `trip/`)
- `modals/` mistura modais de domínios diferentes (search, add location, place detail)

**Proposta de reorganização:**

```
components/
├── map/         # Mapa, controles, marcadores
│   ├── MapContainer.tsx
│   ├── NativeMapContainer.tsx
│   ├── MapControls.tsx
│   └── markers/
├── places/      # Tudo sobre lugares
│   ├── PlaceDetailSheet.tsx
│   ├── PlaceDetailModal.tsx
│   ├── AddLocationModal.tsx
│   └── SearchModal.tsx
├── trips/       # Tudo sobre trips
│   ├── TripPanel.tsx
│   ├── TripBottomBar.tsx
│   ├── TripCallInterface.tsx
│   ├── TripReportModal.tsx
│   ├── TripBookContent.tsx
│   └── IncomingCallModal.tsx
├── social/      # Feed e interações sociais
│   ├── ActivityFeed.tsx
│   ├── TwitterFeed.tsx
│   ├── FeedOverlay.tsx
│   └── CheckInModal.tsx
├── chat/        # Chat de mapa
├── profile/     # Perfil e configurações
├── navigation/  # TopBar, BottomBar, Dock
├── layout/      # Sidebar, Drawer (unificar sidebar/)
└── ui/          # Shadcn
```

---

### A6. 🟡 Falta de Testes

**Situação atual:** O projeto não possui **nenhum teste automatizado** — nem unitário, nem de integração, nem e2e.

**Proposta:**

```
Backend (prioridade):
1. Testes unitários para utils/security.py (hash, tokens)
2. Testes de integração para auth endpoints (signup, login, refresh)
3. Testes de permissões (check_map_access)
4. Framework: pytest + httpx (async)

Frontend (depois):
1. Testes de hooks críticos (useAuth, useMaps)
2. Framework: vitest (já no ecossistema Vite)
```

---

### A7. 🟡 SQLite em Produção

**Arquivo:** `api/app/config.py` (linha 7)

```python
database_url: str = "sqlite+aiosqlite:///./vmaps.db"
```

**Situação:** O default é SQLite, mas em produção (`deploy.sh`, `docker-stack.yaml`) o `.env` pode definir PostgreSQL. Porém, o código tem `PRAGMA journal_mode=WAL` que é SQLite-specific.

**Proposta:**

```
1. Em database.py: condicionar PRAGMA ao SQLite:
   if "sqlite" in database_url:
       await conn.execute(text("PRAGMA journal_mode=WAL"))
2. Documentar no README: "PostgreSQL recomendado em produção"
3. Remover vmaps.db do repo e adicionar ao .gitignore
```

---

## 🧹 Organização de Código

### O1. Unificar Tipos/Interfaces

**Problema:** Tipos estão espalhados em:

- `client/src/lib/api.ts` (inline no arquivo de 1361 linhas)
- `client/src/lib/mockData.ts` (MockUser, MockPlace, etc.)
- Componentes individuais (interfaces inline)

**Proposta:**

```
1. Criar client/src/types/
│   ├── api.ts       # Tipos retornados pela API
│   ├── places.ts    # PlaceData, PlaceCreate, etc.
│   ├── trips.ts     # Trip, TripParticipant, etc.
│   ├── social.ts    # CheckIn, FeedPost, etc.
│   └── index.ts     # Re-exports
```

---

### O2. Limpar TODOs Abandonados

**TODOs encontrados:**

| Arquivo                 | TODO                                               |
| ----------------------- | -------------------------------------------------- |
| `friends.py:73`         | `is_online=False  # TODO: Implement online status` |
| `groups.py:587`         | `# TODO: Check map_members table`                  |
| `GroupsSidebar.tsx:282` | `/* TODO: Share */`                                |
| `TripContext.tsx:311`   | `isOnline: true // TODO: check timestamp`          |
| `TripContext.tsx:314`   | `distanceFromUser: undefined // TODO: calculate`   |

**Proposta:** Criar issues no GitHub para cada TODO ou implementar os mais simples.

---

### O3. Notificação de Teste Hardcoded

**Arquivo:** `client/src/contexts/NotificationContext.tsx` (linhas 97-111)

```typescript
// ❌ Cria notificação de teste toda vez que o array está vazio
if (notifications.length === 0) {
    const testNotification = { type: 'friend_request', ... };
    setNotifications([...prev, testNotification]);
}
```

**Proposta:** Remover completamente. Se necessário para dev, condicionar a `import.meta.env.DEV`.

---

## 📋 Checklist de Implementação

### 🚨 Segurança — Ação Imediata

- [ ] **V1.** Mover Google Maps API key para env var `VITE_GOOGLE_MAPS_API_KEY`
- [ ] **V2.** Remover default da JWT secret key, forçar via `.env`
- [ ] **V3.** Remover traceback da response de erro em produção
- [ ] **V4.** Remover endpoint `/debug/cors-check`

### 🔴 Segurança — Alta Prioridade

- [ ] **V5.** Implementar rate limiting (`slowapi`) nos endpoints de auth
- [ ] **V6.** Adicionar validação de força de senha no signup
- [ ] **V7.** Desabilitar `echo=True` no SQLAlchemy em produção
- [ ] **V8.** Remover emails dos logs de login
- [ ] **V9.** Implementar refresh proativo de tokens
- [ ] **V10.** Remover catch-all route ou retornar 404 real

### 🗑️ Limpeza de Código

- [ ] Deletar 11 scripts loose de migração da raiz da API
- [ ] Deletar diretório `client/src/integrations/supabase/`
- [ ] Remover dados mock de `mockData.ts`, manter apenas helpers
- [ ] Adicionar `vmaps.db*` ao `.gitignore`
- [ ] Remover notificação de teste do `NotificationContext.tsx`
- [ ] Resolver ou documentar TODOs abandonados

### 🏗️ Arquitetura

- [ ] **A1.** Dividir `api.ts` (1361 linhas) em módulos
- [ ] **A2.** Substituir `window.location.reload()` por invalidação de queries
- [ ] **A3.** Unificar lista de CORS origins em settings
- [ ] **A4.** Corrigir `__import__` hack no `auth.py`
- [ ] **A5.** Reorganizar diretório `components/social/` em módulos temáticos
- [ ] **A6.** Adicionar testes automatizados (backend primeiro)
- [ ] **A7.** Condicionar PRAGMA WAL ao SQLite

### 🧹 Organização

- [ ] **O1.** Criar diretório `types/` com interfaces organizadas
- [ ] **O2.** Limpar TODOs ou criar issues
- [ ] **O3.** Remover notificação de teste hardcoded
- [ ] **V11.** Restringir CORS methods/headers
- [ ] **V12.** Proteger diretório de uploads

---

## 🔧 Arquivos Afetados (Resumo)

### Segurança

| Arquivo                                            | Alteração                                                   |
| -------------------------------------------------- | ----------------------------------------------------------- |
| `client/src/components/map/MapContainer.tsx`       | Substituir API key hardcoded por env var                    |
| `client/src/components/social/TripBookContent.tsx` | Substituir API key hardcoded por env var                    |
| `api/app/config.py`                                | Remover default do secret_key, adicionar debug flag         |
| `api/app/main.py`                                  | Remover traceback, debug endpoint, catch-all; unificar CORS |
| `api/app/database.py`                              | Condicionar echo e PRAGMA ao ambiente                       |
| `api/app/routers/auth.py`                          | Rate limit, validação de senha, corrigir **import**         |

### Limpeza

| Arquivo/Diretório                             | Ação                                |
| --------------------------------------------- | ----------------------------------- |
| `api/*.py` (11 scripts)                       | Deletar ou mover para `scripts/`    |
| `api/vmaps.db*`                               | Deletar + `.gitignore`              |
| `client/src/integrations/supabase/`           | Deletar diretório                   |
| `client/src/lib/mockData.ts`                  | Extrair helpers, remover dados mock |
| `client/src/contexts/NotificationContext.tsx` | Remover notificação de teste        |

### Arquitetura

| Arquivo/Diretório                     | Ação                                          |
| ------------------------------------- | --------------------------------------------- |
| `client/src/lib/api.ts`               | Dividir em `api/` com módulos                 |
| `client/src/contexts/TripContext.tsx` | Substituir `window.location.reload()`         |
| `client/src/components/social/`       | Reorganizar em `places/`, `trips/`, `social/` |
| `client/src/types/`                   | Criar diretório de tipos unificados           |
