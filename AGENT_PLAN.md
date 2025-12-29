# Project Plan: Social Map Application Refactor

## 1. Project Context & Goal
We are refactoring a React application into a **Social Mapping Platform** (similar to Zenly or Gyrats). 
**Core Value Proposition:** Users create maps, share them with groups, and interact with locations via a social feed context. 
**Key Feature:** "Trip Mode" (Live location sharing within a group).

## 2. Tech Stack
- **Framework:** Vite + React + TypeScript
- **Styling:** Tailwind CSS
- **UI Library:** Shadcn/ui (Radix Primitives)
- **Icons:** Lucide React
- **Map Engine:** (Preserve current engine, e.g., Leaflet/Mapbox/Google)

## 3. Design System Guidelines (Strict)
- **Visual Style:** "Clean", High Affordance, Modern Mobile-First.
- **Glassmorphism:** Use `bg-background/80 backdrop-blur-md border-white/20` for floating elements over the map.
- **Shape:** Use `rounded-full` for buttons and `rounded-xl` for cards/panels.
- **Z-Index Strategy:** Map is always layer 0. UI controls are floating layers above.
- **Typography:** San Francisco/Inter style. Bold headers, muted metadata (`text-muted-foreground`).

---

## 4. Execution Phases

### PHASE 1: Main Layout & Navigation (The "Floating" UI)
**Goal:** Remove standard sidebars. Maximize map area. Create iOS-style floating controls.

- **Task 1.1:** Refactor `Layout.tsx` so the Map component takes `100vw` and `100vh` absolute positioning.
- **Task 1.2:** Create a `FloatingDock` component fixed at the bottom center.
    - Style: `h-16`, `rounded-full`, `backdrop-blur-md`, `border`, `shadow-lg`.
    - Items: Icons for [My Maps, Explore, Friends, Profile].
    - Interaction: Active state should have a primary color glow or background.
- **Task 1.3:** Create a `TopBar` component (Floating top).
    - Left: Current Map Name (with a dropdown to switch maps).
    - Right: "Start Trip" button (Ghost variant initially).

### PHASE 2: The "Place Feed" (Social Context)
**Goal:** Clicking a place creates a social feed experience, not just a static info window.

- **Task 2.1:** Implement `PlaceDetailSheet` using Shadcn `Sheet` (Side Drawer).
- **Task 2.2:** Structure the Sheet Content:
    - **Header:** Place Name, Star Rating, Category Badge.
    - **Tabs:** Use Shadcn `Tabs` ["Info", "Social"].
- **Task 2.3:** Implement "Social" Tab Content:
    - **Friends Here:** An `AvatarGroup` showing friends currently checked in or who visited recently.
    - **Feed Stream:** A vertical list of `CheckInCard` components.
        - `CheckInCard`: User Avatar + Name + Timestamp + Photo (rounded corners) + Comment.
    - **CTA:** A sticky bottom button "Check-in Here".

### PHASE 3: Map Markers & Social Logic
**Goal:** Distinguish visually between static places and live friends.

- **Task 3.1:** Create `PlaceMarker` component.
    - Visual: Minimalist pin containing an Icon (Restaurant, Park, etc.).
    - Action: Opens `PlaceDetailSheet`.
- **Task 3.2:** Create `FriendMarker` component.
    - Visual: User Avatar (`rounded-full`) with a colored border (`border-primary`).
    - Animation: Add a CSS pulse effect (`animate-pulse` on the ring) if the user is "Active/Online".
    - Label: Small text pill below avatar with name (e.g., "Gabriel").

### PHASE 4: "Trip Mode" (Live Interaction)
**Goal:** A distinct UI mode when a group outing starts.

- **Task 4.1:** Create a global state `isTripActive`.
- **Task 4.2:** Transform UI when `isTripActive === true`:
    - **Top Bar:** Becomes a green/active status bar: "Trip in Progress • 02:30h".
    - **Bottom Dock:** Replaced by `ActiveTripHUD`.
        - `ActiveTripHUD`: A horizontal scroll list of Friends in the trip.
        - Each item shows: Avatar + Distance relative to current user (e.g., "200m away").
    - **Floating Action:** Add a "Recenter Group" button that fits the map bounds to include all friends.

---

## 5. Development Instructions for Agent
1. **Analyze:** Check existing components before creating new ones to avoid duplication.
2. **Shadcn:** Always check if a Shadcn component (like `Sheet`, `Tabs`, `Avatar`, `Badge`) can solve the UI need before building custom divs.
3. **Mocking:** Since backend might not be ready, create a `mockData.ts` file with fake users, places, and check-ins to demonstrate the UI.
4. **Responsiveness:** Ensure all floating elements have safe margins on Mobile (safe-area-inset).