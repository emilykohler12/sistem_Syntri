<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
    <div class="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
      <div class="flex items-center gap-6">
        <router-link to="/" class="font-semibold text-[var(--color-accent)]">Sistem Syntri</router-link>
        <nav class="flex items-center gap-4 text-sm">
          <router-link
            to="/"
            class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
            active-class="!text-[var(--color-text)] font-medium"
            exact-active-class="!text-[var(--color-text)] font-medium"
          >
            Mensajes
          </router-link>
          <router-link
            v-if="auth.isAdmin"
            to="/admin"
            class="text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
            active-class="!text-[var(--color-text)] font-medium"
          >
            Admin
          </router-link>
        </nav>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <span class="text-[var(--color-text-muted)]">
          {{ auth.username }}
          <span v-if="auth.isAdmin" class="ml-1 rounded bg-[var(--color-accent-soft)] px-1.5 py-0.5 text-xs text-[var(--color-accent)]">admin</span>
        </span>
        <button
          class="rounded-md border border-[var(--color-border)] px-3 py-1.5 hover:bg-[var(--color-bg)]"
          @click="handleLogout"
        >
          Salir
        </button>
      </div>
    </div>
  </header>
</template>
