# 🗺️ LUME: Plano Mestre de Identidade Visual

## 🌈 Resumo da Identidade
O LUME abandona o visual genérico de mapas para uma estética de "Instrumento Celeste". O app alterna entre dois estados de espírito que mudam radicalmente a paleta, os mapas e até as mascotes.

---

## 📅 Roadmap de Implementação

### 🟦 Fase 1: Setup do Tema & Infraestrutura (Agora)
- [ ] Criar `ThemeContext.tsx` para alternância Sol/Astra.
- [ ] Configurar tokens de cores no `tailwind.config.js`.
- [ ] Importar fontes *Quicksand* e *JetBrains Mono*.

### 🟧 Fase 2: Interface "Lume OS" (Interface)
- [ ] Criar o **Interruptor Celeste** (Animação de Transição).
- [ ] Refatorar o **Dock Flutuante** (Estilo Cápsula).
- [ ] Estilizar os **Place Sheets** (Cartão Postal vs HUD Espacial).

### 🌌 Fase 3: A Experiência do Mapa (Geo-Design)
- [ ] Implementar Estilo "Lume Day" no Google Maps.
- [ ] Implementar Estilo "Lume Night" (Astra) com brilho neon.
- [ ] Criar marcadores personalizados (Gota Coral e Avatars Personagens).

### ✨ Fase 4: Personalidade & Mascotes (UX)
- [ ] Desenvolver Splash Screen com órbitas.
- [ ] Implementar Loading States (Sol pulando corda / Astra no telescópio).
- [ ] Adicionar diálogos das mascotes nos "Empty States".

---

## 🎨 Guia de Estilo Rápido

### Modo SOL (Dia)
- **Vibe:** Ensolarado, amigável, analógico.
- **Cores:** Creme (#FDFBF7), Coral (#FF6B6B), Tinta (#1C1917).
- **Mapa:** Ruas claras, caminhos estilo "canetinha".

### Modo ASTRA (Noite)
- **Vibe:** Tecnológico, profundo, neon.
- **Cores:** Espaço (#0F172A), Gold (#FACC15), Cyan (#22D3EE).
- **Mapa:** Escuro, lugares brilhando como estrelas, rotas neon.

---

## 🛠️ Notas Técnicas
- **Storage:** O tema deve ser salvo no `localStorage`.
- **Animações:** Prioridade de uso para `framer-motion` para transições de UI.
- **Performance:** Os estilos JSON do mapa devem ser carregados sob demanda para evitar overhead.
