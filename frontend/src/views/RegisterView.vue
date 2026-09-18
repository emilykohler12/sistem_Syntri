<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

async function handleSubmit() {
  error.value = ''

  if (password.value !== confirmPassword.value) {
    error.value = 'Las contraseñas no coinciden.'
    return
  }

  loading.value = true
  try {
    await auth.register(username.value.trim(), password.value)
    toast.success('Cuenta creada. Ya podés iniciar sesión.')
    router.push({ name: 'login' })
  } catch (err) {
    error.value = extractErrorMessage(err, 'No se pudo registrar el usuario.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-6">
        <h1 class="text-2xl font-semibold text-[var(--color-text)]">Crear cuenta</h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1">Registrate en Sistem Syntri</p>
      </div>

      <form
        class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 shadow-sm space-y-4"
        @submit.prevent="handleSubmit"
      >
        <div v-if="error" class="rounded-md bg-[var(--color-danger-soft)] text-[var(--color-danger)] text-sm px-3 py-2">
          {{ error }}
        </div>

        <div class="space-y-1">
          <label class="text-sm font-medium" for="username">Usuario</label>
          <input
            id="username"
            v-model="username"
            required
            autofocus
            class="w-full rounded-md border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/40"
          />
        </div>

        <div class="space-y-1">
          <label class="text-sm font-medium" for="password">Contraseña</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            class="w-full rounded-md border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/40"
          />
        </div>

        <div class="space-y-1">
          <label class="text-sm font-medium" for="confirm">Confirmar contraseña</label>
          <input
            id="confirm"
            v-model="confirmPassword"
            type="password"
            required
            class="w-full rounded-md border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/40"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-md bg-[var(--color-accent)] text-white py-2 text-sm font-medium hover:bg-[var(--color-accent-hover)] disabled:opacity-60"
        >
          {{ loading ? 'Creando cuenta…' : 'Registrarme' }}
        </button>

        <p class="text-center text-sm text-[var(--color-text-muted)]">
          ¿Ya tenés cuenta?
          <router-link to="/login" class="text-[var(--color-accent)] hover:underline">Iniciá sesión</router-link>
        </p>
      </form>
    </div>
  </div>
</template>
