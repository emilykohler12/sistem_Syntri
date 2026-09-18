# System Syntri — Frontend

Panel web para System Syntri: envío de mensajes a Slack/Discord/Telegram, autenticación por email con recuperación de contraseña, y administración (usuarios, roles con permisos configurables, límites, métricas con gráficos).

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
├── views/                 # Páginas (login, registro, recuperar contraseña, mensajes, admin/*)
├── components/            # Componentes reutilizables (NavBar, AuthShell, DailyActivityChart, ...)
├── stores/                # Pinia: auth (sesión/JWT/permisos) y toast (notificaciones)
├── router/                # Rutas y guards (auth / permisos por sección de admin)
├── lib/api.ts              # Cliente axios (interceptores de token y errores)
└── types/                  # Tipos TS que reflejan los schemas del backend
```

El login del backend devuelve solo un JWT (sin endpoint `/me`), así que el email, el rol y los permisos del usuario se leen decodificando el propio token.

## Roles y permisos

El panel de administración se adapta al rol de quien inició sesión: cada pestaña (Mensajes, Métricas, Usuarios, Roles, Límites) solo aparece si el rol tiene el permiso correspondiente. `admin` siempre tiene acceso total; los demás roles se configuran desde la pestaña Roles.
