<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { extractErrorMessage } from '@/lib/api'
import AuthShell from '@/components/AuthShell.vue'

const email = ref('')
const loading = ref(false)
const error = ref('')
const sent = ref(false)

const auth = useAuthStore()
const router = useRouter()

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.forgotPassword(email.value.trim())
    sent.value = true
  } catch (err) {
    error.value = extractErrorMessage(err, 'No se pudo procesar el pedido.')
  } finally {
    loading.value = false
  }
}

function goToReset() {
  router.push({ name: 'reset-password', query: { email: email.value.trim() } })
}
</script>

<template>
  <AuthShell title="Recuperar contraseña" subtitle="Te mandamos un código de 6 dígitos a tu correo">
    <form v-if="!sent" class="space-y-4" @submit.prevent="handleSubmit">
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

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? 'Enviando…' : 'Enviar código' }}
      </button>

      <p class="text-center text-sm text-[var(--color-text-muted)]">
        <router-link to="/login" class="text-[var(--color-accent)] font-medium hover:underline">Volver a iniciar sesión</router-link>
      </p>
    </form>

    <div v-else class="space-y-4 text-center">
      <div class="rounded-lg bg-[var(--color-success-soft)] text-[var(--color-success)] text-sm px-3 py-2.5">
        Si <strong>{{ email }}</strong> está registrado, te enviamos un código de 6 dígitos. Vence en 15 minutos.
      </div>
      <button class="btn-primary w-full" @click="goToReset">
        Ya tengo el código
      </button>
    </div>
  </AuthShell>
</template>
