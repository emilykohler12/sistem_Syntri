<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { extractErrorMessage } from '@/lib/api'
import AuthShell from '@/components/AuthShell.vue'

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.push(redirect)
  } catch (err) {
    error.value = extractErrorMessage(err, 'No se pudo iniciar sesión.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell title="Bienvenido" subtitle="Iniciá sesión para seguir enviando notificaciones">
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <div v-if="error" class="rounded-lg bg-[var(--color-danger-soft)] text-[var(--color-danger)] text-sm px-3 py-2.5">
        {{ error }}
      </div>

      <div class="space-y-1.5">
        <label class="text-sm font-medium text-[var(--color-text)]" for="email">Correo electrónico</label>
        <input
          id="email"
          v-model="email"
          type="email"
          required
          autofocus
          placeholder="vos@ejemplo.com"
          class="input"
        />
      </div>

      <div class="space-y-1.5">
        <div class="flex items-center justify-between">
          <label class="text-sm font-medium text-[var(--color-text)]" for="password">Contraseña</label>
          <router-link to="/forgot-password" class="text-xs text-[var(--color-accent)] hover:underline">
            ¿Olvidaste tu contraseña?
          </router-link>
        </div>
        <input id="password" v-model="password" type="password" required placeholder="••••••••" class="input" />
      </div>

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? 'Ingresando…' : 'Ingresar' }}
      </button>

      <p class="text-center text-sm text-[var(--color-text-muted)]">
        ¿No tenés cuenta?
        <router-link to="/register" class="text-[var(--color-accent)] font-medium hover:underline">Registrate</router-link>
      </p>
    </form>
  </AuthShell>
</template>
