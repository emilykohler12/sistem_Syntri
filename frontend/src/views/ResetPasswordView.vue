<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import AuthShell from '@/components/AuthShell.vue'
import PasswordInput from '@/components/PasswordInput.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const email = ref(typeof route.query.email === 'string' ? route.query.email : '')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''

  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Las contraseñas no coinciden.'
    return
  }
  if (newPassword.value.length < 6) {
    error.value = 'La contraseña debe tener al menos 6 caracteres.'
    return
  }

  loading.value = true
  try {
    await auth.resetPassword(email.value.trim(), code.value.trim(), newPassword.value)
    toast.success('Contraseña actualizada. Ya podés iniciar sesión.')
    router.push({ name: 'login' })
  } catch (err) {
    error.value = extractErrorMessage(err, 'Código inválido o vencido.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell title="Elegí una nueva contraseña" subtitle="Ingresá el código de 6 dígitos que te enviamos por email">
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <div v-if="error" class="rounded-lg bg-[var(--color-danger-soft)] text-[var(--color-danger)] text-sm px-3 py-2.5">
        {{ error }}
      </div>

      <div class="space-y-1.5">
        <label class="text-sm font-medium text-[var(--color-text)]" for="email">Correo electrónico</label>
        <input id="email" v-model="email" type="email" required placeholder="vos@ejemplo.com" class="input" />
      </div>

      <div class="space-y-1.5">
        <label class="text-sm font-medium text-[var(--color-text)]" for="code">Código de 6 dígitos</label>
        <input
          id="code"
          v-model="code"
          type="text"
          inputmode="numeric"
          maxlength="6"
          required
          placeholder="123456"
          class="input text-center tracking-[0.4em] font-mono text-lg"
        />
      </div>

      <div class="space-y-1.5">
        <label class="text-sm font-medium text-[var(--color-text)]" for="new-password">Nueva contraseña</label>
        <PasswordInput id="new-password" v-model="newPassword" required placeholder="Mínimo 6 caracteres" autocomplete="new-password" />
      </div>

      <div class="space-y-1.5">
        <label class="text-sm font-medium text-[var(--color-text)]" for="confirm">Confirmar contraseña</label>
        <PasswordInput id="confirm" v-model="confirmPassword" required placeholder="••••••••" autocomplete="new-password" />
      </div>

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? 'Guardando…' : 'Cambiar contraseña' }}
      </button>

      <p class="text-center text-sm text-[var(--color-text-muted)]">
        <router-link to="/forgot-password" class="text-[var(--color-accent)] hover:underline">Pedir un código nuevo</router-link>
        ·
        <router-link to="/login" class="text-[var(--color-accent)] hover:underline">Volver a iniciar sesión</router-link>
      </p>
    </form>
  </AuthShell>
</template>
