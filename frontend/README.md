# Sistem Syntri — Frontend

Panel web para Sistem Syntri: envío de mensajes a Slack/Discord y administración (usuarios, roles, límites, métricas).

Vue 3 + TypeScript + Vite + Tailwind CSS v4 + Pinia + Vue Router + Axios.

## Setup

```bash
npm install
cp .env.example .env   # ajustá VITE_API_URL si el backend no corre en localhost:8000
npm run dev
```

La app queda disponible en `http://localhost:5173`. Necesita el backend de `sistem_Syntri` corriendo (ver el README de la raíz del repo).

## Scripts

- `npm run dev` — servidor de desarrollo
- `npm run build` — build de producción (incluye chequeo de tipos con `vue-tsc`)
- `npm run preview` — sirve el build de producción localmente

## Estructura

```
src/
├── views/            # Páginas (login, registro, mensajes, admin/*)
├── components/       # Componentes reutilizables (NavBar, StatusBadge, ToastHost)
├── stores/           # Pinia: auth (sesión/JWT) y toast (notificaciones)
├── router/           # Rutas y guards (auth / admin)
├── lib/api.ts        # Cliente axios (interceptores de token y errores)
└── types/            # Tipos TS que reflejan los schemas del backend
```

El login del backend devuelve solo un JWT (sin endpoint `/me`), así que el usuario y el rol se leen decodificando el propio token.
