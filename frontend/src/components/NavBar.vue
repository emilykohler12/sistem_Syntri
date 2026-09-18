<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import logoIcon from '@/assets/logo-icon.png'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-[var(--color-border)] bg-[var(--color-surface)]/90 backdrop-blur">
    <div class="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
      <div class="flex items-center gap-8">
        <router-link to="/" class="cursor-default flex items-center gap-2 font-semibold text-[var(--color-text)]">
          <img :src="logoIcon" alt="" class="h-8 w-8 rounded-lg" />
          System Syntri
        </router-link>
        <nav class="flex items-center gap-1 text-sm">
          <router-link
            to="/"
            class="cursor-default px-3 py-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg)]"
            active-class="!text-[var(--color-accent)] !bg-[var(--color-accent-soft)] font-medium"
            exact-active-class="!text-[var(--color-accent)] !bg-[var(--color-accent-soft)] font-medium"
          >
            Mensajes
          </router-link>
          <router-link
            v-if="auth.isAdmin"
            to="/admin"
            class="cursor-default px-3 py-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg)]"
            active-class="!text-[var(--color-accent)] !bg-[var(--color-accent-soft)] font-medium"
          >
            Admin
          </router-link>
        </nav>
      </div>
      <div class="flex items-center gap-3 text-sm">
        <div class="hidden sm:flex items-center gap-2 text-[var(--color-text-muted)]">
          <span class="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--color-accent-soft)] text-[var(--color-accent)] text-xs font-semibold uppercase">
            {{ auth.email?.[0] ?? '?' }}
          </span>
          <span class="max-w-[180px] truncate">{{ auth.email }}</span>
          <span v-if="auth.isAdmin" class="rounded-full bg-[var(--color-accent-soft)] px-2 py-0.5 text-xs font-medium text-[var(--color-accent)]">
            admin
          </span>
        </div>
        <button
          class="cursor-pointer rounded-md border border-[var(--color-border)] px-3 py-1.5 text-[var(--color-text-muted)] hover:bg-[var(--color-bg)] hover:text-[var(--color-text)]"
          @click="handleLogout"
        >
          Salir
        </button>
      </div>
    </div>
  </header>
</template>
