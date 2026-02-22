# 🗺️ V-Maps (LUME) — Planner de Finalização Android

> **Objetivo:** Mapear todas as funcionalidades existentes na versão web que ainda faltam na versão Android, com foco nas **interações dentro do mapa** para exibição de informações dos lugares marcados.

---

## 📊 Visão Geral: Web vs Android

A aplicação Android é empacotada via **Capacitor** (WebView), mas o mapa utiliza o plugin nativo `@capacitor/google-maps`, que renderiza **por baixo da WebView**. Isso significa que os componentes React da web que ficam _sobre_ o mapa (overlays, modals, sheets) funcionam normalmente, mas o **mapa em si** e seus **marcadores** são nativos e precisam de tratamento especial.

| Funcionalidade                              | Web (`MapContainer.tsx`)                     | Android (`NativeMapContainer.tsx`)             | Status     |
| ------------------------------------------- | -------------------------------------------- | ---------------------------------------------- | ---------- |
| Mapa Google Maps                            | ✅ `@vis.gl/react-google-maps`               | ✅ `@capacitor/google-maps`                    | ✅ OK      |
| Marcadores customizados (ícone, cor, hover) | ✅ `AdvancedMarker` com HTML/CSS             | ❌ Apenas marcador padrão                      | 🔴 Falta   |
| Label do lugar no hover                     | ✅ Tooltip com nome aparece no hover         | ❌ Sem suporte a hover (touch)                 | 🔴 Falta   |
| Click no marcador → detalhe do lugar        | ✅ `onLocationClick` abre `PlaceDetailSheet` | ⚠️ `onMarkerClick` existe mas fluxo incompleto | 🟡 Parcial |
| Marcador de localização do usuário (pulse)  | ✅ Div animado azul com ping                 | ❌ Sem marcador de usuário diferenciado        | 🔴 Falta   |
| Marcadores de participantes de Trip         | ✅ Avatar, nome, status indicator            | ❌ Marcador genérico sem avatar                | 🔴 Falta   |
| Centralizar no usuário                      | ✅ Botão `Navigation` com `panTo`            | ❌ Sem botão de centralização                  | 🔴 Falta   |
| Ajustar bounds (fitBounds)                  | ✅ `BoundsController` quando muda mapa       | ⚠️ `setCamera` básico (centro + zoom fixo)     | 🟡 Parcial |
| Modo "Adicionar" (crosshair)                | ✅ Cursor crosshair + tooltip                | ❌ Sem modo adicionar via mapa                 | 🔴 Falta   |
| Tema dia/noite                              | ✅ `dayStyles` / `nightStyles`               | ⚠️ Apenas `dayStyles` aplicado                 | 🟡 Parcial |

---

## 🎯 Funcionalidades Dentro do Mapa — Detalhamento

### 1. 🔴 Clique no Marcador → Detalhe do Lugar (`PlaceDetailSheet`)

**O que existe na web:**
Ao clicar em um marcador no mapa, o componente `PlaceDetailSheet` abre como um painel lateral (Sheet) contendo:

- **Cabeçalho:** Ícone de categoria, nome do lugar, rating em estrelas, badge de categoria
- **Aba "Informações":**
  - Endereço completo
  - Descrição do lugar
  - Botão "Navegar até aqui" (abre Google Maps externo)
- **Aba "Social":**
  - Lista de amigos que já estiveram no lugar (avatar group)
  - Feed de check-ins com: avatar do usuário, username, tempo relativo, rating (estrelas), comentário, foto
  - Botões de "Curtir" e "Comentar" em cada check-in
- **Footer fixo:**
  - Botão "Fazer Check-in"
  - Botão "Remover do Mapa" (para o dono do place, com confirmação)

**O que existe no Android:**
O `NativeMapContainer` dispara `onMarkerClick` que retorna `markerId` e `metadata`. No `MapContainer.tsx` (linha 271-278), há lógica para encontrar o `location` e chamar `onLocationClick`. Porém, **o marcador nativo do Capacitor não renderiza o HTML customizado** — ele usa marcadores genéricos do Google Maps.

**O que falta implementar no Android:**

1. **Garantir que `onMarkerClick` propaga corretamente para abrir `PlaceDetailSheet`**
   - O mapeamento `markerIdToMetadata` pode falhar se marcadores forem re-adicionados (IDs mudam)
   - Precisa de cleanup adequado de marcadores antigos antes de adicionar novos

2. **`PlaceDetailSheet` precisa funcionar em tela mobile**
   - O Sheet abre pelo lado `right` — no mobile deveria abrir de baixo para cima (`bottom`)
   - Precisa ajustar para aparecer acima do mapa nativo (z-index do WebView)

3. **Fetch de check-ins do lugar precisa funcionar no Android**
   - A URL da API precisa apontar para o servidor remoto (`tsapi.ciano.io`), não `localhost`

**Passos para implementar:**

```
Passo 1: Verificar o fluxo onMarkerClick
├── Confirmar que metadata.type === 'place' está sendo passado
├── Confirmar que onLocationClick é chamado com o location correto
└── Testar se PlaceDetailSheet abre no Android

Passo 2: Ajustar PlaceDetailSheet para mobile
├── Mudar SheetContent side="right" → side="bottom" quando isMobile
├── Ajustar altura máxima (70-80vh)
├── Garantir que o backdrop aparece sobre o mapa nativo
└── Testar scroll das tabs no mobile

Passo 3: Ajustar fetch de check-ins
├── Verificar que api.getCheckIns usa a URL correta no Android
├── Testar carregamento de fotos dos check-ins
└── Confirmar formatação de datas com date-fns/ptBR
```

---

### 2. 🔴 Marcadores Customizados de Lugares

**O que existe na web:**
Cada marcador é um `AdvancedMarker` com HTML custom:

- Círculo de 40px com ícone `MapPin`
- Cor muda com tema: `bg-brand-core text-white` (sol) / `bg-slate-900 border-brand-accent` (lua)
- **Tooltip flutuante** com nome do lugar aparece no hover (`group-hover:opacity-100`)
- Transição `scale-110` no hover

**O que existe no Android:**
Marcadores genéricos do Google Maps — ícone padrão vermelho, sem customização visual.

**O que falta implementar no Android:**

O plugin `@capacitor/google-maps` suporta `iconUrl` nos marcadores. Podemos usar isso para dar identidade visual.

**Passos para implementar:**

```
Passo 1: Criar ícones de marcador como imagem
├── Gerar ícones SVG/PNG para marcadores de lugar
├── Hospedar as imagens no bundle (pasta public/ ou assets/)
└── Criar variantes para tema dia/noite

Passo 2: Aplicar iconUrl nos marcadores
├── No NativeMapContainer, ao mapear filteredLocations:
│   └── Adicionar iconUrl: '/assets/marker-place-day.png'
├── Diferenciar marcadores por tipo via metadata
└── Testar renderização no Android

Passo 3: Alternativa — InfoWindow no click
├── Como não há hover no mobile, ao clicar no marcador:
│   └── Opção A: Abrir PlaceDetailSheet diretamente (já parcialmente implementado)
│   └── Opção B: Mostrar InfoWindow nativo com nome + botão "Ver mais"
└── Decidir abordagem (Opção A é mais consistente com a web)
```

---

### 3. 🔴 Marcador de Localização do Usuário

**O que existe na web:**

- Círculo azul pulsante (`bg-blue-500 animate-pulse`)
- Ring externo com `animate-ping` para efeito de radar
- Posição atualizada via `useGeolocation`

**O que existe no Android:**
O usuário é adicionado como marcador genérico com `metadata: { type: 'user' }`, sem diferenciação visual.

**Passos para implementar:**

```
Passo 1: Criar ícone customizado para o marcador do usuário
├── Criar imagem PNG de um ponto azul com borda branca
├── Ou usar iconUrl com SVG data URI
└── Tamanho recomendado: 24x24px ou 32x32px

Passo 2: Aplicar no NativeMapContainer
├── No mapeamento de markers, quando metadata.type === 'user':
│   └── Definir iconUrl: '/assets/marker-user.png'
└── Testar que aparece diferente dos marcadores de lugar

Passo 3: Habilitar watchPosition nativo
├── Usar @capacitor/geolocation para tracking contínuo
├── Atualizar posição do marcador em tempo real
└── Garantir que permissões de localização estão configuradas no AndroidManifest
```

---

### 4. 🔴 Marcadores de Participantes de Trip

**O que existe na web:**

- Avatar circular de 48px com foto do perfil ou iniciais
- Borda colorida: `border-brand-accent` (usuário atual) / `border-emerald-500` (outros)
- Ping animation para o usuário atual
- Status indicator (bolinha verde) no canto superior direito
- Label com nome no hover
- Posição baseada em `activeTrip.locations` (última localização registrada)

**O que existe no Android:**
Os participantes são mapeados como marcadores genéricos com `metadata: { type: 'participant' }`, sem avatar ou diferenciação.

**Passos para implementar:**

```
Passo 1: Criar ícones de marcador para participantes
├── Gerar ícone genérico de participante (silhueta colorida)
├── Idealmente: renderizar avatar do usuário em Canvas → export como data URI
│   └── Mas isso é complexo no contexto nativo
└── Alternativa simples: usar ícone de pessoa colorido

Passo 2: Diferenciar marcadores por tipo de participante
├── Usuário atual: iconUrl azul/ciano
├── Outros participantes: iconUrl verde
└── Aplicar no array de markers do NativeMapContainer

Passo 3: Atualização em tempo real da posição
├── Usar o polling existente de trip locations
├── Ao receber novas localizações, atualizar markers
├── Limpar marcadores antigos antes de adicionar novos (evitar duplicatas)
└── Testar com trip ativa no Android
```

---

### 5. 🟡 Ajustar Bounds ao Trocar de Mapa (fitBounds)

**O que existe na web:**
O `BoundsController` monitora `selectedGroupId` e quando muda:

- Filtra locations do mapa selecionado
- Se 1 lugar: `panTo` + zoom 16
- Se múltiplos: `fitBounds` com padding (50px, 400px para sidebar)

**O que existe no Android:**
O `NativeMapContainer` faz `setCamera` com zoom fixo 12 (múltiplos) ou 15 (único). Não calcula bounds reais.

**Passos para implementar:**

```
Passo 1: Receber mudança de mapa selecionado
├── Quando selectedGroupId muda, filteredLocations muda
├── NativeMapContainer já re-renderiza markers via useEffect[markers]
└── O cálculo de centro já existe mas é impreciso

Passo 2: Calcular zoom adequado
├── Para 1 marcador: zoom 15 ✅ (já funciona)
├── Para múltiplos: calcular zoom baseado na distância entre pontos
│   ├── Usar fórmula: zoom = log2(360 / max(deltaLat, deltaLng)) + 1
│   └── Ou usar a API nativa de padding se disponível
└── Aplicar com setCamera({ coordinate, zoom, animate: true })

Passo 3: Adicionar padding para elementos de UI
├── Considerar TopBar e BottomBar ao calcular bounds
└── Testar com diferentes quantidades de marcadores
```

---

### 6. 🔴 Modo "Adicionar Lugar" no Mapa

**O que existe na web:**

- Botão `MapPin` flutuante no canto inferior direito
- Toggle de modo "adicionar": cursor vira crosshair
- Tooltip "Clique no mapa para adicionar"
- Ao clicar no mapa: abre `AddLocationModal` com coordenadas

**O que existe no Android:**
Não há tratamento para clique no mapa no `NativeMapContainer`. Apenas clique em marcadores é tratado.

**Passos para implementar:**

```
Passo 1: Adicionar listener de clique no mapa
├── Usar googleMapRef.current.setOnMapClickListener()
├── Receber lat/lng do ponto clicado
└── Propagar para o componente pai via callback

Passo 2: Definir prop onMapClick no NativeMapContainer
├── Adicionar onMapClick?: (lat: number, lng: number) => void
├── Na inicialização do mapa, registrar o listener
└── Chamar onMapClick com as coordenadas recebidas

Passo 3: Integrar com AddLocationModal
├── No MapContainer, quando isNative:
│   └── Passar onMapClick para NativeMapContainer
├── Ao receber click, chamar handleMapClick (já existente no Index)
├── AddLocationModal abre com coordenadas (já funciona)
└── Testar fluxo completo: click → modal → salvar → marcador aparece
```

---

### 7. 🟡 Tema Dia/Noite no Mapa Nativo

**O que existe na web:**

- `theme === 'sol'` aplica `dayStyles` (cores quentes, fundo claro)
- `theme !== 'sol'` aplica `nightStyles` (cores frias, fundo escuro)
- Background do mapa muda com o tema

**O que existe no Android:**
Apenas `dayStyles` é aplicado na inicialização do mapa. Não reage a mudança de tema.

**Passos para implementar:**

```
Passo 1: Receber tema como prop
├── Adicionar theme: string ao NativeMapContainerProps
└── Passar theme do contexto ThemeContext

Passo 2: Aplicar estilos baseado no tema
├── Na criação do mapa: styles: theme === 'sol' ? dayStyles : nightStyles
├── Quando tema muda: precisaria recriar o mapa ou usar setMapStyle
│   └── Verificar se @capacitor/google-maps suporta setMapStyle dinâmico
└── Se não suportar, recriar o mapa (destroy + create)

Passo 3: Testar transição de tema
├── Trocar tema no app e verificar se mapa atualiza
└── Verificar que marcadores continuam visíveis com ambos os temas
```

---

### 8. 🔴 Centralizar no Usuário (Botão de Navegação)

**O que existe na web:**

- Botão flutuante com ícone `Navigation`
- Ao clicar: `panTo(userLocation)` + toast de confirmação
- Loading state enquanto obtém localização
- Se localização negada: toast de erro

**O que existe no Android:**
Não há botão de centralização. O mapa inicia centrado na última posição conhecida.

**Passos para implementar:**

```
Passo 1: Expor função de centralização no NativeMapContainer
├── Adicionar método ou prop: centerOnLocation?: { lat, lng } | null
├── Quando mudar, chamar googleMapRef.current.setCamera({ coordinate, zoom: 15 })
└── Animar a transição (animate: true)

Passo 2: O botão já existe no MapContainer.tsx
├── O botão "Centralizar" (linhas 411-422) é renderizado fora da branch nativa
├── Precisa ser renderizado TAMBÉM quando isNative === true
├── O botão é um overlay HTML, funciona sobre o mapa nativo
└── Verificar z-index do botão vs WebView

Passo 3: Conectar botão ao mapa nativo
├── Ao clicar no botão, passar userLocation como prop de centralização
├── NativeMapContainer reage e faz setCamera
└── Testar no Android com localização real
```

---

### 9. � Refatoração Total do Sistema de WebSockets

> **Esta é uma refatoração transversal** que afeta tanto a camada de mapa quanto todas as funcionalidades sociais e de trip. É fundamental para o funcionamento correto no Android.

#### 9.1. Arquitetura Atual — Diagnóstico

A comunicação em tempo real está **fragmentada** em 3 abordagens diferentes, causando inconsistência e problemas no Android:

| Feature                                        | Mecanismo Atual                                        | Problema                                               |
| ---------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------ |
| **Notificações gerais**                        | ✅ WebSocket via `NotificationContext.tsx`             | URL de WS não funciona corretamente no Capacitor       |
| **Trip events** (inicio, fim, convites)        | ✅ WebSocket (pub/sub via `NotificationContext`)       | Funciona, mas depende da conexão WS estar ativa        |
| **Trip locations** (posição dos participantes) | ✅ WebSocket `location_updated` + polling 30s fallback | Polling 30s é muito lento para tracking real-time      |
| **Trip chat**                                  | ⚠️ WebSocket `chat_message` + carga inicial via API    | Mensagens podem se perder se WS desconectar            |
| **Chat de mapa** (`useChat.ts`)                | ❌ Apenas polling 5s                                   | Consome bateria, latência alta, sem WS                 |
| **Check-ins** (`useCheckIns.ts`)               | ❌ Nenhum real-time                                    | Comentário no código: "atualizações só ao recarregar"  |
| **Feed social** (`TwitterFeed.tsx`)            | ⚠️ WS `new_post` mostra toast, mas não atualiza feed   | Feed precisa ser recarregado manualmente               |
| **Amizades**                                   | ✅ WS `friend_request` / `friend_request_accepted`     | Toast funciona, mas lista não atualiza automaticamente |

#### 9.2. Problema Crítico no Android: URL do WebSocket

**Arquivo:** `client/src/contexts/NotificationContext.tsx` (linhas 117-125)

```typescript
// ❌ PROBLEMA: Dentro do Capacitor, window.location.hostname é "localhost"
// mesmo que a app esteja rodando nativamente no dispositivo.
const isProduction = window.location.hostname !== "localhost";

// No Android com Capacitor, hostname = "localhost" → entra no branch dev
// → tenta conectar ws://localhost:8000 → FALHA (não há servidor local)
```

**A URL do WebSocket precisa ser construída de forma diferente no Capacitor**, considerando:

- `Capacitor.isNativePlatform()` para detectar ambiente nativo
- Usar a URL do servidor remoto sempre no nativo
- Considerar `capacitor.config.ts` → `server.hostname`

#### 9.3. Pontos que Necessitam de Atualização em Tempo Real

##### A) Localização dos participantes de Trip (CRÍTICO para Android)

**Situação atual:** O backend envia `location_updated` via WS em `trips.py` (linha 631). O `TripContext.tsx` escuta via `subscribeToGlobalEvents` e atualiza `realTimeLocations`. Fallback: polling a cada 30s.

**Problemas:**

- No Android, se o WS cair, o polling de 30s é **muito lento** para tracking de participantes
- O app precisa enviar sua localização via `api.updateTripLocation()` — não existe listener de geolocation nativo contínuo
- Quando o app vai para background no Android, o WS desconecta e o tracking para

**Refatoração necessária:**

```
Passo 1: Corrigir conexão WS no Capacitor
├── Detectar isNative via Capacitor.isNativePlatform()
├── Usar URL remota (wss://tsapi.ciano.io/vmaps/users/ws) sempre no nativo
└── Adicionar reconexão automática com backoff exponencial

Passo 2: Implementar geolocation contínua no Android
├── Usar @capacitor/geolocation watchPosition
├── Enviar localização via API a cada 10s (quando trip ativa)
├── Manter um serviço de foreground para tracking em background
└── Parar tracking quando trip encerrar

Passo 3: Reduzir polling de trip para 15s (fallback)
├── Se WS ativo: não fazer polling
├── Se WS desconectado: polling a cada 15s
└── Ao reconectar WS, parar polling
```

##### B) Chat de Mapa (REFATORAR para usar WS)

**Situação atual:** `useChat.ts` usa polling a cada 5 segundos. O próprio código comenta: _"Em produção, considere usar WebSocket"_.

**Problemas:**

- Consome bateria excessivamente no Android (request HTTP a cada 5s)
- Latência de até 5s para novas mensagens
- Múltiplos intervalos ativos se o usuário navegar entre mapas

**Refatoração necessária:**

```
Passo 1: Backend — broadcast de chat de mapa via WS
├── Em chat.py, após salvar mensagem já faz broadcast ✅ (linha 145)
├── Verificar que o tipo 'chat_message' inclui map_id
└── Confirmar que broadcast vai para todos os membros do mapa

Passo 2: Frontend — useChat subscreve ao WS
├── Remover polling (setInterval de 5s)
├── Usar subscribeToGlobalEvents do NotificationContext
├── Filtrar mensagens por map_id
├── Adicionar mensagem recebida via WS ao state local
└── Manter fetch inicial para carregar histórico

Passo 3: Testar no Android
├── Abrir chat em 2 dispositivos
├── Enviar mensagem → deve aparecer instantaneamente no outro
└── Verificar que não há polling ativo (checar DevTools Network)
```

##### C) Check-ins (ADICIONAR real-time)

**Situação atual:** `useCheckIns.ts` (linha 83): _"Removido polling — atualizações só ao recarregar página"_. O backend (`check_ins.py`, linha 222) já faz `broadcast_to_friends`, mas o frontend ignora.

**Refatoração necessária:**

```
Passo 1: Frontend — escutar eventos de check-in via WS
├── Em useCheckIns ou no NotificationContext:
│   └── Quando receber evento tipo 'new_post' ou 'check_in':
│       └── Re-fetch check-ins ou adicionar ao state
├── Atualizar PlaceDetailSheet (aba Social) automaticamente
└── Atualizar ActivityFeed se estiver aberto

Passo 2: Backend — verificar payload do broadcast
├── Confirmar que check_ins.py envia dados suficientes:
│   └── { type: 'new_post', check_in_id, place_id, user_id, ... }
└── Garantir que broadcast_to_friends inclui o próprio usuário
```

##### D) Feed Social (ATUALIZAR automaticamente)

**Situação atual:** O WS envia `new_post` e o `NotificationContext` mostra um toast, mas o feed (`TwitterFeed.tsx`) não recarrega automaticamente. O usuário precisa fechar e abrir o feed.

**Refatoração necessária:**

```
Passo 1: TwitterFeed subscreve a eventos de WS
├── Usar subscribeToGlobalEvents dentro do TwitterFeed
├── Quando receber 'new_post': chamar loadFeed() novamente
├── Quando receber 'post_like': atualizar contagem local
└── Quando receber 'post_comment': atualizar contagem local

Passo 2: Invalidar cache do react-query
├── Usar queryClient.invalidateQueries({ queryKey: ['feed'] })
├── Ou emitir evento custom que o hook de feed escute
└── Garantir que não refaz fetch excessivamente (debounce de 2s)
```

##### E) Mapas e Places (SINCRONIZAR entre dispositivos)

**Situação atual:** O backend faz `broadcast_to_friends` em `maps.py` quando um novo mapa é criado. Mas **adicionar/remover places não notifica ninguém**.

**Refatoração necessária:**

```
Passo 1: Backend — broadcast quando place é criado/removido
├── Em places.py ou maps.py:
│   └── Após criar place: broadcast para membros do mapa
│   └── Após deletar place: broadcast para membros do mapa
├── Tipo de evento: 'place_created' / 'place_deleted'
└── Incluir map_id no payload

Passo 2: Frontend — reagir a eventos de place
├── Em useMaps: escutar 'place_created' e 'place_deleted'
├── Re-fetch places ou atualizar state local
└── Marcadores no mapa nativo se atualizam automaticamente (via re-render)
```

#### 9.4. Refatoração do ConnectionManager (Backend)

**Arquivo:** `api/app/utils/websockets.py`

**Problemas atuais:**

- Sem heartbeat/ping-pong → conexões mortas não são detectadas
- Sem reconexão → se cair, fica morto
- `broadcast_to_friends` faz query SQL síncrona dentro do broadcast → lento
- Sem rooms/channels → tudo passa pelo mesmo pipe global

**Refatoração necessária:**

```
Passo 1: Adicionar heartbeat (ping/pong)
├── Backend envia "ping" a cada 30s
├── Se não receber "pong" em 10s → remove conexão
└── Frontend responde automaticamente (WebSocket nativo já faz)

Passo 2: Implementar sistema de rooms
├── Ao entrar em trip: join_room(f"trip_{trip_id}")
├── Ao abrir mapa: join_room(f"map_{map_id}")
├── Broadcast para room específica (evita broadcast global)
└── Ao sair de trip/mapa: leave_room()

Passo 3: Cachear lista de amigos
├── Não fazer SELECT a cada broadcast_to_friends
├── Manter cache de amizades em memória (invalidar ao aceitar/remover amizade)
└── Ou pré-computar na conexão WS
```

#### 9.5. Refatoração do NotificationContext (Frontend)

**Arquivo:** `client/src/contexts/NotificationContext.tsx`

**Refatoração necessária:**

```
Passo 1: Corrigir URL do WebSocket para Capacitor
├── import { Capacitor } from '@capacitor/core'
├── if (Capacitor.isNativePlatform()):
│   └── wsUrl = 'wss://tsapi.ciano.io/vmaps/users/ws?token=...'
├── else if (isProduction):
│   └── wsUrl = 'wss://tsapi.ciano.io/vmaps/users/ws?token=...'
└── else:
    └── wsUrl = 'ws://localhost:8000/users/ws?token=...'

Passo 2: Adicionar reconexão automática
├── onclose → tentar reconectar após 2s, 4s, 8s, 16s (backoff exponencial)
├── onerror → mesma lógica de reconexão
├── Máximo de 10 tentativas antes de desistir
├── Mostrar indicador visual "Reconectando..." se desconectado por >5s
└── Ao reconectar: re-fetch de notificações pendentes

Passo 3: Adicionar estado de conexão
├── Expor isConnected: boolean no contexto
├── Componentes podem reagir a desconexão (ex: mostrar badge offline)
└── Quando reconectar: invalidar caches que dependem de WS

Passo 4: Lifecycle no Android
├── Quando app vai para foreground: verificar se WS está ativo, reconectar se necessário
├── Quando app vai para background: manter WS se trip ativa, senão desconectar
├── Usar @capacitor/app para detectar lifecycle events
└── Evitar múltiplas conexões WS simultâneas
```

---

## �📋 Checklist de Implementação

### Prioridade Alta (Funcionalidades do Mapa)

- [ ] **1. Clique no marcador → detalhe do lugar** (PlaceDetailSheet funcional no Android)
  - [ ] Verificar fluxo `onMarkerClick` → `onLocationClick` → `PlaceDetailSheet`
  - [ ] Ajustar `PlaceDetailSheet` para mobile (side bottom, altura adequada)
  - [ ] Testar fetch de check-ins via API remota
  - [ ] Testar botão "Navegar até aqui" (deep link Google Maps)
  - [ ] Testar botão "Fazer Check-in" abrindo `CheckInModal`

- [ ] **2. Marcadores customizados** (identidade visual)
  - [ ] Criar ícones PNG: lugar (dia/noite), usuário (azul), participante (verde)
  - [ ] Aplicar `iconUrl` nos marcadores por tipo
  - [ ] Testar renderização no Android

- [ ] **3. Marcador de localização do usuário**
  - [ ] Criar ícone diferenciado
  - [ ] Configurar geolocation do Capacitor corretamente
  - [ ] Testar atualização em tempo real

- [ ] **4. Clique no mapa → adicionar lugar**
  - [ ] Implementar `setOnMapClickListener` no NativeMapContainer
  - [ ] Conectar com `AddLocationModal`
  - [ ] Testar fluxo completo de adição

### Prioridade Alta (WebSocket — Infraestrutura)

- [ ] **9. Refatoração do sistema de WebSockets**
  - [ ] **9a. Corrigir URL do WS para Capacitor** (`NotificationContext.tsx`)
    - [ ] Detectar nativo via `Capacitor.isNativePlatform()`
    - [ ] Usar URL remota no nativo
    - [ ] Testar conexão WS no Android
  - [ ] **9b. Reconexão automática com backoff**
    - [ ] Implementar retry com backoff exponencial (2s, 4s, 8s...)
    - [ ] Expor `isConnected` no contexto
    - [ ] Mostrar indicador de reconexão
  - [ ] **9c. Lifecycle Android (foreground/background)**
    - [ ] Usar `@capacitor/app` para detectar lifecycle
    - [ ] Reconectar WS ao voltar para foreground
    - [ ] Evitar múltiplas conexões simultâneas
  - [ ] **9d. Migrar `useChat.ts` de polling para WS**
    - [ ] Remover `setInterval` de 5s
    - [ ] Subscrever a `chat_message` via WS
    - [ ] Manter fetch inicial para histórico
  - [ ] **9e. Adicionar real-time a check-ins**
    - [ ] Escutar `new_post` para atualizar `useCheckIns` e `PlaceDetailSheet`
  - [ ] **9f. Atualizar feed social automaticamente**
    - [ ] `TwitterFeed` recarrega ao receber `new_post`
    - [ ] Atualizar likes/comments via `post_like` / `post_comment`
  - [ ] **9g. Sincronizar places entre dispositivos**
    - [ ] Backend: broadcast ao criar/deletar place
    - [ ] Frontend: `useMaps` escuta eventos de place

### Prioridade Média (UX e Polish)

- [ ] **5. Botão de centralizar no usuário**
  - [ ] Expor `setCamera` via prop/ref no NativeMapContainer
  - [ ] Renderizar botão flutuante no modo nativo
  - [ ] Testar centralização com animação

- [ ] **6. Bounds automáticos ao trocar mapa**
  - [ ] Melhorar cálculo de zoom para múltiplos marcadores
  - [ ] Adicionar padding para UI elements
  - [ ] Testar com 1, 5, e 20+ marcadores

- [ ] **7. Tema dia/noite no mapa nativo**
  - [ ] Receber tema como prop
  - [ ] Aplicar `dayStyles` ou `nightStyles` dinamicamente
  - [ ] Testar transição de tema

### Prioridade Média (WebSocket — Backend)

- [ ] **10. Refatorar ConnectionManager**
  - [ ] Adicionar heartbeat ping/pong (30s)
  - [ ] Implementar rooms/channels para trip e mapa
  - [ ] Cachear lista de amigos (evitar SELECT a cada broadcast)
  - [ ] Limpar conexões mortas automaticamente

### Prioridade Baixa (Trip Features)

- [ ] **8. Marcadores de participantes de Trip**
  - [ ] Ícones diferenciados por tipo de participante
  - [ ] Atualização em tempo real da posição
  - [ ] Testar com trip ativa

- [ ] **11. Geolocation contínua no Android para Trips**
  - [ ] `@capacitor/geolocation` watchPosition
  - [ ] Enviar localização a cada 10s durante trip
  - [ ] Foreground service para tracking em background

---

## 🔧 Arquivos Afetados

### Funcionalidades do Mapa

| Arquivo                                             | Tipo       | Alteração                                                       |
| --------------------------------------------------- | ---------- | --------------------------------------------------------------- |
| `client/src/components/map/NativeMapContainer.tsx`  | 🔄 Alterar | Adicionar `onMapClick`, tema, ícones custom, `centerOnLocation` |
| `client/src/components/map/MapContainer.tsx`        | 🔄 Alterar | Renderizar botões flutuantes no modo nativo, passar novas props |
| `client/src/components/social/PlaceDetailSheet.tsx` | 🔄 Alterar | Adaptar para mobile (side bottom), ajustar responsividade       |
| `client/src/pages/Index.tsx`                        | 🔄 Alterar | Conectar `onMapClick` nativo ao `handleMapClick`                |
| `client/public/assets/`                             | 🆕 Criar   | Ícones PNG para marcadores (lugar, usuário, participante)       |

### WebSocket e Real-Time

| Arquivo                                        | Tipo         | Alteração                                                       |
| ---------------------------------------------- | ------------ | --------------------------------------------------------------- |
| `client/src/contexts/NotificationContext.tsx`  | 🔄 Refatorar | Corrigir URL Capacitor, reconexão automática, lifecycle Android |
| `client/src/hooks/useChat.ts`                  | 🔄 Refatorar | Remover polling 5s, migrar para WS via NotificationContext      |
| `client/src/hooks/useCheckIns.ts`              | 🔄 Alterar   | Adicionar listener de WS para novos check-ins                   |
| `client/src/hooks/useMaps.ts`                  | 🔄 Alterar   | Escutar eventos de place criado/deletado via WS                 |
| `client/src/hooks/useTrips.ts`                 | 🔄 Alterar   | Reduzir polling fallback de 30s para 15s                        |
| `client/src/contexts/TripContext.tsx`          | 🔄 Alterar   | Melhorar lógica de reconexão, geolocation contínua              |
| `client/src/components/social/TwitterFeed.tsx` | 🔄 Alterar   | Auto-reload ao receber `new_post` via WS                        |
| `api/app/utils/websockets.py`                  | 🔄 Refatorar | Heartbeat, rooms/channels, cache de amigos                      |
| `api/app/routers/places.py` ou `maps.py`       | 🔄 Alterar   | Broadcast ao criar/deletar place                                |

---

## 📝 Notas Técnicas

### Limitações do `@capacitor/google-maps`

1. **Sem AdvancedMarker**: O plugin nativo não suporta HTML custom nos marcadores. Apenas `iconUrl` para ícones estáticos.
2. **Sem hover**: Em dispositivos touch, não há conceito de hover. Interação é via tap (click).
3. **Mapa renderiza atrás da WebView**: O mapa nativo é desenhado _por baixo_ da WebView. Elementos HTML (modals, sheets, botões) aparecem por cima automaticamente, desde que o background da WebView seja transparente.
4. **Marker IDs mudam**: Ao adicionar novos marcadores, os IDs nativos são regenerados. O mapeamento `markerIdToMetadata` precisa ser limpo e recriado a cada atualização.

### WebSocket no Capacitor — Considerações Especiais

1. **URL de conexão**: `window.location.hostname` dentro do Capacitor retorna `localhost` (por causa do `server.hostname` em `capacitor.config.ts`). A detecção de ambiente precisa usar `Capacitor.isNativePlatform()` em vez de checar hostname.
2. **Lifecycle do app**: No Android, quando o app vai para background, a WebView pode ser suspensa após ~5 minutos. O WS desconecta silenciosamente. Ao retornar ao foreground, é necessário verificar e reconectar.
3. **Foreground Service**: Para trips com tracking ativo, considerar usar um foreground service nativo (plugin Capacitor customizado) para manter a conexão WS e o envio de localização mesmo com o app em background.
4. **Bateria**: Trocar polling por WS reduz significativamente o consumo de bateria. O `useChat.ts` com polling de 5s é especialmente problemático no Android.

### Mapa de Eventos WebSocket (Backend → Frontend)

| Evento                               | Origem (Backend) | Destino (Frontend)                      | Status Atual   |
| ------------------------------------ | ---------------- | --------------------------------------- | -------------- |
| `trip_updated`                       | `trips.py`       | `TripContext.tsx`                       | ✅ Funciona    |
| `trip_ended`                         | `trips.py`       | `TripContext.tsx`                       | ✅ Funciona    |
| `trip_invite` / `trip_call_incoming` | `trips.py`       | `TripContext.tsx` (IncomingCallModal)   | ✅ Funciona    |
| `location_updated`                   | `trips.py`       | `TripContext.tsx` → `realTimeLocations` | ✅ Funciona    |
| `chat_message` (trip)                | `chat.py`        | `TripContext.tsx` → `chatMessages`      | ✅ Funciona    |
| `chat_message` (map)                 | `chat.py`        | `useChat.ts`                            | ❌ Usa polling |
| `new_post` (check-in)                | `check_ins.py`   | `NotificationContext` (toast apenas)    | ⚠️ Parcial     |
| `friend_request`                     | `friends.py`     | `NotificationContext` (toast)           | ✅ Toast OK    |
| `friend_request_accepted`            | `friends.py`     | `NotificationContext` (toast)           | ✅ Toast OK    |
| `post_like`                          | —                | `NotificationContext` (toast)           | ⚠️ Toast only  |
| `post_comment`                       | —                | `NotificationContext` (toast)           | ⚠️ Toast only  |
| `place_created`                      | —                | —                                       | ❌ Não existe  |
| `place_deleted`                      | —                | —                                       | ❌ Não existe  |

### Considerações de Performance

- No Android, evitar re-renderizar todos os marcadores a cada mudança de state
- Usar `removeMarkers` antes de `addMarkers` para evitar acúmulo
- Considerar debounce na atualização de marcadores se houver polling frequente (trips)
- Trocar polling por WS reduz requests HTTP e consumo de bateria

### Permissões Android (AndroidManifest.xml)

Verificar que as seguintes permissões estão configuradas:

```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_LOCATION" />
```
