<script setup lang="ts">
const tabs = [
  { to: { name: 'admin-metrics' }, label: 'Métricas' },
  { to: { name: 'admin-messages' }, label: 'Mensajes' },
  { to: { name: 'admin-users' }, label: 'Usuarios' },
  { to: { name: 'admin-roles' }, label: 'Roles' },
  { to: { name: 'admin-limits' }, label: 'Límites' },
]
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-8 space-y-6">
    <h1 class="text-2xl font-semibold">Panel de administración</h1>

    <nav class="flex gap-1 border-b border-[var(--color-border)]">
      <router-link
        v-for="tab in tabs"
        :key="tab.label"
        :to="tab.to"
        class="px-3 py-2 text-sm text-[var(--color-text-muted)] border-b-2 border-transparent hover:text-[var(--color-text)]"
        active-class="!text-[var(--color-accent)] !border-[var(--color-accent)] font-medium"
      >
        {{ tab.label }}
      </router-link>
    </nav>

    <router-view />
  </div>
</template>
