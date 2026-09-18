<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const ALL_TABS = [
  { to: { name: 'admin-metrics' }, label: 'Métricas', permission: 'metrics' },
  { to: { name: 'admin-messages' }, label: 'Mensajes', permission: 'messages' },
  { to: { name: 'admin-users' }, label: 'Usuarios', permission: 'users' },
  { to: { name: 'admin-roles' }, label: 'Roles', permission: 'roles' },
  { to: { name: 'admin-limits' }, label: 'Límites', permission: 'limits' },
]

const tabs = computed(() => ALL_TABS.filter((tab) => auth.hasPermission(tab.permission)))
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
