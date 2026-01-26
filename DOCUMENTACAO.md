# 🗺️ V-Maps: Social Mapping Platform

## 🎯 Objetivos da Aplicação
O **V-Maps** é uma plataforma de mapeamento social projetada para transformar a maneira como as pessoas interagem com lugares e amigos. O objetivo principal é criar um ecossistema onde o mapa não é apenas uma ferramenta de navegação, mas um contexto para interação social em tempo real.

Os pilares do projeto são:
- **Contexto Social:** Unir a localização geográfica com feeds de atividades de amigos.
- **Interação em Tempo Real:** Compartilhamento de localização ativa durante eventos sociais (Trips).
- **Personalização:** Permitir que usuários e grupos criem seus próprios "universos" de mapas com lugares curados.

---

## 🚀 Funcionalidades Principais

### 1. Mapas Interativos e Personalizados
- **Criação de Mapas:** Usuários podem criar múltiplos mapas temáticos (ex: "Melhores Cafés", "Picos de Skate").
- **Marcadores de Lugares:** Adição de locais específicos com ícones personalizados.
- **Centralização Automática:** O mapa ajusta automaticamente o zoom para mostrar todos os pontos de um mapa selecionado.

### 2. Interface "Floating UI" (Mobile-First)
- **Dock Flutuante:** Navegação estilo iOS na parte inferior para acesso rápido a Mapas, Explorar, Amigos e Perfil.
- **Top Bar Dinâmico:** Barra superior flutuante que mostra o contexto atual (nome do mapa ou status de uma "Trip").
- **Glassmorphism:** Interface moderna com efeitos de desfoque (backdrop-blur) para maximizar a visibilidade do mapa.

### 3. Feed Social e Check-ins
- **Social Place Sheet:** Ao clicar em um lugar, abre-se um painel com informações e um feed social.
- **Check-ins com Avaliação:** Usuários podem registrar visitas, adicionar fotos, descrições e avaliações (1-5 estrelas).
- **Feed de Atividades:** Visualização de posts das visitas recentes de amigos em um estilo de rede social moderna.

### 4. Sistema de Grupos
- **Colaboração:** Criação de grupos de amigos para compartilhamento de mapas específicos.
- **Gerenciamento de Membros:** Convite e remoção de participantes em grupos privados.
- **Mapas de Grupo:** Lugares sugeridos e visitados por qualquer membro do grupo aparecem para todos.

### 5. Modo "Trip" (Viagem/Role em Grupo)
- **Tracking Ativo:** Compartilhamento de localização em tempo real para os membros de uma "Trip" ativa.
- **Trip HUD:** Interface dedicada que mostra a distância entre os participantes e o tempo decorrido.
- **Marcadores Animados:** Avatares dos amigos pulsando no mapa quando estão online e em movimento.

---

## 🛠️ Stack Tecnológica
- **Backend:** Python (FastAPI), SQLAlchemy para banco de dados, Alembic para migrações e Socket.io para atualizações em tempo real.
- **Frontend:** React + TypeScript + Vite, estilizado com Tailwind CSS e Shadcn/UI para componentes de interface premium.
- **Mapas:** Google Maps SDK integrado com React.

---

## 🔮 Próximos Passos (Roadmap)

### Curto Prazo (Ajustes e Polimento)
- [ ] **Integração de Compartilhamento:** Finalizar a funcionalidade de compartilhar um mapa individual já existente com um grupo criado posteriormente.
- [ ] **Polimento do Modo Trip:** Refinar a precisão do tracking de localização e suavizar as animações dos marcadores de amigos.
- [ ] **Notificações:** Implementar alertas push/in-app para quando um amigo fizer check-in em um lugar próximo.

### Médio Prazo (Novas Funcionalidades)
- [ ] **Sugestões por IA:** Implementar um recomendador que sugere novos lugares baseando-se no histórico de check-ins do usuário e de seus amigos.
- [ ] **Filtros Avançados:** Busca de lugares por tags sociais (ex: "Onde meus amigos mais foram este mês").
- [ ] **Websockets:** Migrar totalmente o polling de localização para WebSockets para reduzir latência e consumo de bateria/dados.

### Longo Prazo (Expansão)
- [ ] **Aplicativo Nativo:** Portar a interface web para um app mobile nativo (React Native) para melhor aproveitamento de sensores de localização.
- [ ] **Eventos Públicos:** Suporte para "Zonas de Calor" em eventos de grande escala no mapa.
- [ ] **Eventos do aplicativo:** Eventos criados para gamefização do jogo como descobrir lugares novos, visitar lugares com amigos, etc.