# V-Maps - Planner de Atualizações

## 📋 Resumo dos Problemas e Funcionalidades

### 🐛 Bugs a Corrigir
1. **Check-in não é adicionado à lista** - Após criar um check-in, ele não aparece no feed
7. **Check-in POST não é chamado** - A rota POST não está sendo chamada ao criar check-in no feed
8. **Avaliação estática no feed** - A avaliação deve ser dinâmica (puxar existente ou aguardar nova)

### ✨ Novas Funcionalidades
2. **Editar/Deletar Mapas** - Permitir edição e exclusão de mapas
3. **Feed de Check-ins como Posts** - Exibir com imagem, descrição e avaliação
4. **Centralizar Mapa no Mapa Selecionado** - Ao selecionar um mapa, centralizar nas localizações
5. **Sistema de Trips** - Iniciar viagens com amigos, visualizar localização em tempo real
6. **Sistema de Grupos** - Criar grupos na sessão de amigos com mapas compartilhados
9. **Remover Places de Mapas** - Permitir deletar lugares de um mapa
10. **Compartilhar Mapa com Grupo** - Compartilhar mapa existente com grupo (não só criar)

---

## 🔧 Detalhamento Técnico

---

### 1. 🐛 Bug: Check-in não adicionado à lista

**Problema:** O check-in é criado no backend mas não atualiza a lista no frontend.

**Causa provável:** O `useCheckIns` usa polling de 10s, mas após criar um check-in a lista não é atualizada imediatamente.

#### Backend (Verificar)
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `api/app/routers/check_ins.py` | ✅ Verificar | Confirmar que retorna o check-in com `profile` e `place` |

#### Frontend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `client/src/hooks/useCheckIns.ts` | 🔄 Alterar | Após `createCheckIn`, garantir que o novo check-in é adicionado com dados completos |
| `client/src/pages/Index.tsx` | ✅ Verificar | Confirmar que `handleCheckIn` está chamando corretamente |

**Tarefas:**
- [ ] Verificar resposta do endpoint `POST /check-ins` no backend
- [ ] Garantir que `apiToCheckIn` converte corretamente os dados
- [ ] Adicionar `refetch()` após criar check-in se necessário

---

### 2. ✨ Editar/Deletar Mapas

**Situação atual:** Backend já tem endpoints, frontend parcialmente implementado.

#### Backend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `api/app/routers/maps.py` | ✅ Já existe | `PUT /maps/{id}` e `DELETE /maps/{id}` |

#### Frontend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `client/src/lib/api.ts` | ✅ Verificar | `updateMap` e `deleteMap` já existem |
| `client/src/hooks/useMaps.ts` | ✅ Verificar | `updateMap` e `deleteMap` já implementados |
| `client/src/components/sidebar/DynamicSidebar.tsx` | 🔄 Alterar | Adicionar opções no dropdown menu de cada mapa |

**Tarefas:**
- [ ] Adicionar modal de edição de mapa (nome, ícone)
- [ ] Adicionar confirmação antes de deletar
- [ ] Conectar ao dropdown menu existente

---

### 3. ✨ Feed de Check-ins como Posts (com Avaliação)

**Situação atual:** Feed existe mas está simples. Falta campo de avaliação (rating).

#### Backend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `api/app/models/check_in.py` | 🔄 Alterar | Adicionar campo `rating: int` (1-5 estrelas) |
| `api/app/schemas/check_in.py` | 🔄 Alterar | Adicionar `rating` ao schema |
| `api/app/routers/check_ins.py` | 🔄 Alterar | Aceitar `rating` na criação |
| `alembic/versions/` | 🆕 Criar | Nova migration para adicionar coluna `rating` |

#### Frontend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `client/src/lib/api.ts` | 🔄 Alterar | Adicionar `rating` ao `CheckInResponse` |
| `client/src/hooks/useCheckIns.ts` | 🔄 Alterar | Adicionar `rating` ao interface `CheckIn` |
| `client/src/components/social/CheckInModal.tsx` | 🔄 Alterar | Adicionar seletor de estrelas (1-5) |
| `client/src/components/social/ActivityFeed.tsx` | 🔄 Alterar | Exibir rating com estrelas, melhorar layout de post |

**Tarefas:**
- [ ] Criar migration Alembic para campo `rating`
- [ ] Atualizar model e schema no backend
- [ ] Criar componente `StarRating` no frontend
- [ ] Atualizar CheckInModal para incluir avaliação
- [ ] Redesenhar ActivityFeed como posts estilo Instagram/social

---

### 4. ✨ Centralizar Mapa ao Selecionar

**Situação atual:** Ao selecionar um mapa na sidebar, o mapa interativo não muda.

#### Frontend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `client/src/pages/Index.tsx` | 🔄 Alterar | Calcular centro das localizações do mapa selecionado |
| `client/src/components/map/MapContainer.tsx` | 🔄 Alterar | Adicionar prop para ajustar bounds/zoom automaticamente |
| `client/src/components/sidebar/DynamicSidebar.tsx` | 🔄 Alterar | Ao clicar no mapa, notificar para centralizar |

**Tarefas:**
- [ ] Criar função `calculateBounds(places)` para calcular área que contém todos os lugares
- [ ] Usar `map.fitBounds()` do Google Maps para ajustar visualização
- [ ] Passar callback `onMapSelect` da Index para DynamicSidebar

---

### 7. 🐛 Check-in POST não é chamado

**Situação atual:** Ao criar um check-in no feed, a rota POST não está sendo chamada.

#### Frontend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `client/src/components/sidebar/DynamicSidebar.tsx` | 🔄 Alterar | Verificar se `CheckInModal` está conectado corretamente |
| `client/src/components/social/CheckInModal.tsx` | 🔄 Alterar | Garantir que `onSubmit` chama o endpoint POST |
| `client/src/hooks/useCheckIns.ts` | 🔄 Alterar | Verificar implementação de `createCheckIn` |

**Tarefas:**
- [ ] Verificar se o modal está sendo aberto corretamente
- [ ] Verificar se o `onSubmit` está chamando `createCheckIn`
- [ ] Garantir que `createCheckIn` faz POST para `/check-ins`
- [ ] Testar fluxo completo de criação

---

### 8. ✨ Remover Places de Mapas

**Situação atual:** Não há como remover um lugar de um mapa após adicioná-lo.

#### Backend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `api/app/routers/places.py` | 🔄 Alterar | Adicionar `DELETE /places/{id}` |

#### Frontend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `client/src/lib/api.ts` | 🔄 Alterar | Adicionar `deletePlace(id)` |
| `client/src/hooks/useMaps.ts` | 🔄 Alterar | Adicionar função para deletar place |
| `client/src/components/sidebar/DynamicSidebar.tsx` | 🔄 Alterar | Adicionar botão de remover em cada place |
| `client/src/components/modals/PlaceDetailModal.tsx` | 🔄 Alterar | Adicionar opção de remover no modal |

**Tarefas:**
- [ ] Implementar endpoint DELETE no backend
- [ ] Adicionar função no hook
- [ ] Adicionar UI para remover (X ou menu)
- [ ] Atualizar lista após remoção

---

### 9. ✨ Compartilhar Mapa com Grupo

**Situação atual:** Mapas só podem ser criados com grupos, não compartilhados depois.

#### Backend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `api/app/routers/maps.py` | 🔄 Alterar | Adicionar `POST /maps/{id}/share-with-group` |

#### Frontend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `client/src/lib/api.ts` | 🔄 Alterar | Adicionar `shareMapWithGroup(mapId, groupId)` |
| `client/src/hooks/useMaps.ts` | 🔄 Alterar | Adicionar função de compartilhamento |
| `client/src/components/sidebar/DynamicSidebar.tsx` | 🔄 Alterar | Adicionar opção "Compartilhar com Grupo" no dropdown |
| `client/src/components/modals/ShareMapModal.tsx` | 🆕 Criar | Modal para selecionar grupo para compartilhar |

**Tarefas:**
- [ ] Implementar endpoint de compartilhamento
- [ ] Criar modal de seleção de grupo
- [ ] Adicionar opção no menu dropdown do mapa
- [ ] Atualizar estado após compartilhamento

---

### 10. 🐛 Avaliação Dinâmica no Feed

**Situação atual:** A avaliação é estática e não reflete o estado real (existente ou aguardando).

#### Frontend
| Arquivo | Status | Alteração |
|---------|--------|-----------|
| `client/src/components/sidebar/DynamicSidebar.tsx` | 🔄 Alterar | Exibir avaliação existente ou "Aguardando avaliação" |
| `client/src/components/ui/star-rating.tsx` | 🔄 Alterar | Suportar estado "vazio/pendente" |

**Tarefas:**
- [ ] Se check-in tem rating, exibir estrelas preenchidas
- [ ] Se check-in não tem rating, exibir "Aguardando avaliação" ou estrelas vazias
- [ ] Permitir adicionar avaliação posteriormente

---

### 5. ✨ Sistema de Trips (Viagens em Grupo)

**Nova funcionalidade complexa.** Permite iniciar viagens com amigos e ver localização em tempo real.

#### Backend - Novos Models
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `api/app/models/trip.py` | 🆕 Criar | Model `Trip` (id, name, map_id, owner_id, status, started_at, ended_at) |
| `api/app/models/trip_participant.py` | 🆕 Criar | Model `TripParticipant` (trip_id, user_id, current_lat, current_lng, last_updated) |

#### Backend - Schemas
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `api/app/schemas/trip.py` | 🆕 Criar | Schemas para Trip e TripParticipant |

#### Backend - Routers
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `api/app/routers/trips.py` | 🆕 Criar | CRUD de trips + endpoints de localização |

**Endpoints necessários:**
```
POST   /trips                    - Criar trip
GET    /trips                    - Listar minhas trips
GET    /trips/{id}               - Detalhes da trip
PUT    /trips/{id}               - Atualizar trip
DELETE /trips/{id}               - Deletar trip
POST   /trips/{id}/start         - Iniciar trip
POST   /trips/{id}/end           - Encerrar trip
POST   /trips/{id}/participants  - Adicionar participante
DELETE /trips/{id}/participants/{user_id} - Remover participante
PUT    /trips/{id}/location      - Atualizar minha localização
GET    /trips/{id}/locations     - Obter localizações de todos
```

#### Frontend
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `client/src/lib/api.ts` | 🔄 Alterar | Adicionar endpoints de trips |
| `client/src/hooks/useTrips.ts` | 🆕 Criar | Hook para gerenciar trips |
| `client/src/components/trips/TripModal.tsx` | 🆕 Criar | Modal para criar/gerenciar trip |
| `client/src/components/trips/TripPanel.tsx` | 🆕 Criar | Painel mostrando trip ativa |
| `client/src/components/trips/ParticipantMarker.tsx` | 🆕 Criar | Marcador no mapa para cada participante |
| `client/src/components/map/MapContainer.tsx` | 🔄 Alterar | Exibir marcadores de participantes |
| `client/src/components/sidebar/DynamicSidebar.tsx` | 🔄 Alterar | Adicionar seção/botão de Trips |

**Tarefas:**
- [ ] Criar models Trip e TripParticipant no backend
- [ ] Criar migration Alembic
- [ ] Criar router de trips com todos endpoints
- [ ] Criar hook useTrips no frontend
- [ ] Criar UI para criar trip (selecionar amigos ou grupo)
- [ ] Criar painel de trip ativa com lista de participantes
- [ ] Implementar atualização de localização em tempo real (polling ou websocket)
- [ ] Exibir marcadores de participantes no mapa

---

### 6. ✨ Sistema de Grupos (na Sessão de Amigos)

**Nova funcionalidade.** Grupos permitem organizar amigos e ter mapas compartilhados.

#### Backend - Novos Models
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `api/app/models/group.py` | 🆕 Criar | Model `Group` (id, name, icon, owner_id, map_id, created_at) |
| `api/app/models/group_member.py` | 🆕 Criar | Model `GroupMember` (group_id, user_id, role, joined_at) |

#### Backend - Schemas
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `api/app/schemas/group.py` | 🆕 Criar | Schemas para Group e GroupMember |

#### Backend - Routers
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `api/app/routers/groups.py` | 🆕 Criar | CRUD de grupos + membros |

**Endpoints necessários:**
```
POST   /groups                  - Criar grupo (cria mapa automaticamente)
GET    /groups                  - Listar meus grupos
GET    /groups/{id}             - Detalhes do grupo
PUT    /groups/{id}             - Atualizar grupo
DELETE /groups/{id}             - Deletar grupo
POST   /groups/{id}/members     - Adicionar membro
DELETE /groups/{id}/members/{user_id} - Remover membro
POST   /groups/{id}/leave       - Sair do grupo
```

#### Frontend
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `client/src/lib/api.ts` | 🔄 Alterar | Adicionar endpoints de groups |
| `client/src/hooks/useGroups.ts` | 🆕 Criar | Hook para gerenciar grupos |
| `client/src/components/groups/GroupModal.tsx` | 🆕 Criar | Modal para criar/editar grupo |
| `client/src/components/groups/GroupList.tsx` | 🆕 Criar | Lista de grupos |
| `client/src/components/sidebar/DynamicSidebar.tsx` | 🔄 Alterar | Adicionar tab/seção de Grupos na FriendsPanel |

**Tarefas:**
- [ ] Criar models Group e GroupMember no backend
- [ ] Criar migration Alembic
- [ ] Criar router de groups com todos endpoints
- [ ] Criar hook useGroups no frontend
- [ ] Criar modal de criação de grupo (nome, ícone, selecionar amigos)
- [ ] Adicionar lista de grupos na FriendsPanel
- [ ] Integrar grupos com sistema de trips

---

## 📅 Ordem de Implementação Sugerida

### Fase 1: Correções e Melhorias Básicas (1-2 dias)
1. ✅ Corrigir bug do check-in não aparecer na lista
2. ✅ Implementar editar/deletar mapas na UI
3. ✅ Centralizar mapa ao selecionar

### Fase 2: Sistema de Avaliação (1 dia)
4. ✅ Adicionar rating aos check-ins (backend)
5. ✅ Atualizar feed com layout de posts e estrelas

### Fase 2.5: Correções Intermediárias (0.5-1 dia)
6. ✅ Corrigir check-in POST não sendo chamado (preservar map_id ao selecionar place)
7. ✅ Implementar remoção de places dos mapas (botão no PlaceDetailSheet)
8. 🔄 Implementar compartilhamento de mapa com grupo (depende da Fase 3)
9. ✅ Fazer avaliação dinâmica no feed (StarRating aceita null, exibe "Aguardando avaliação")

### Fase 3: Grupos (2-3 dias)
10. ✅ Criar backend de grupos
11. ✅ Criar frontend de grupos
12. ✅ Integrar grupos com mapas

### Fase 4: Trips (3-4 dias)
13. ✅ Criar backend de trips
14. ✅ Criar frontend de trips
15. ✅ Implementar tracking de localização
16. ✅ Exibir participantes no mapa

---

## 🗂️ Estrutura de Arquivos Final

### Backend (novos arquivos)
```
api/app/
├── models/
│   ├── trip.py           🆕
│   ├── trip_participant.py 🆕
│   ├── group.py          🆕
│   └── group_member.py   🆕
├── schemas/
│   ├── trip.py           🆕
│   └── group.py          🆕
└── routers/
    ├── trips.py          🆕
    └── groups.py         🆕
```

### Frontend (novos arquivos)
```
client/src/
├── hooks/
│   ├── useTrips.ts       🆕
│   └── useGroups.ts      🆕
├── components/
│   ├── trips/
│   │   ├── TripModal.tsx      🆕
│   │   ├── TripPanel.tsx      🆕
│   │   └── ParticipantMarker.tsx 🆕
│   ├── groups/
│   │   ├── GroupModal.tsx     🆕
│   │   └── GroupList.tsx      🆕
│   └── ui/
│       └── StarRating.tsx     🆕
```

---

## 📝 Notas Técnicas

### Localização em Tempo Real (Trips)
- **Opção 1:** Polling a cada 5-10 segundos (mais simples)
- **Opção 2:** WebSocket com `fastapi-websocket` (melhor UX)
- Usar `navigator.geolocation.watchPosition()` no frontend

### Database Migrations
Todas as novas tabelas precisam de migrations Alembic:
1. `trips` - Viagens
2. `trip_participants` - Participantes + localização
3. `groups` - Grupos de amigos
4. `group_members` - Membros dos grupos
5. `check_ins.rating` - Nova coluna de avaliação

### Considerações de Segurança
- Apenas owner pode deletar trips/grupos
- Validar que usuário pertence ao grupo/trip antes de acessar
- Rate limiting para atualizações de localização
- Limitar participantes por trip (ex: máximo 10)

---

## ✅ Checklist de Conclusão

- [x] Bug check-in corrigido (retorna dados completos)
- [x] Editar/deletar mapas funcionando
- [x] Feed com avaliação (estrelas)
- [x] Mapa centraliza ao selecionar
- [x] Check-in POST sendo chamado corretamente (preserva map_id)
- [x] Remover places de mapas funcionando (botão no PlaceDetailSheet)
- [ ] Compartilhar mapa com grupo funcionando (depende Fase 3)
- [x] Avaliação dinâmica no feed (StarRating aceita null)
- [ ] Sistema de grupos implementado
- [ ] Sistema de trips implementado
- [ ] Tracking de localização funcionando
- [ ] Testes básicos realizados
- [ ] Deploy atualizado
